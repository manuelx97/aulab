import os
import uuid
from pathlib import Path

import chromadb
import chainlit as cl
import ollama
from chromadb.utils import embedding_functions
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = BASE_DIR / "resumes"
COLLECTION_NAME = "CVs"
EMBEDDING_MODEL = "text-embedding-3-small"
OLLAMA_MODEL = "llama3.2"

load_dotenv(BASE_DIR / ".env")

collection = None


def load_documents():
    documents = []
    metadatas = []
    ids = []

    for file_path in sorted(DOCUMENTS_DIR.glob("*.txt")):
        text = file_path.read_text(encoding="utf-8")
        chunks = [
            chunk.strip()
            for chunk in text.replace("\n", ".").split("### ")
            if chunk.strip()
        ]

        for chunk in chunks:
            documents.append(chunk)
            metadatas.append({"source": file_path.name})
            ids.append(str(uuid.uuid4()))

    return documents, metadatas, ids


def get_collection():
    global collection

    if collection is not None:
        return collection

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise RuntimeError(
            "OPENAI_API_KEY non trovata. Impostala prima di avviare l'app."
        )

    documents, metadatas, ids = load_documents()
    if not documents:
        raise RuntimeError("Nessun curriculum trovato nella cartella resumes.")

    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=openai_key,
        model_name=EMBEDDING_MODEL,
    )

    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=openai_ef,
    )
    collection.add(documents=documents, metadatas=metadatas, ids=ids)

    return collection


def read_first_lines(file_path: Path, limit: int = 100):
    lines = []

    with file_path.open("r", encoding="utf-8") as file:
        for index, line in enumerate(file):
            if index >= limit:
                break
            lines.append(line.strip())

    return lines


def get_candidate_name(context):
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    "Dato il seguente contesto individua il nome e cognome "
                    "del candidato e ritorna solo il nome e cognome del candidato. "
                    f"Il contesto e' l'inizio del curriculum vitae: {context}"
                ),
            }
        ],
    )

    return response["message"]["content"]


def create_prompt(context, question, candidate_name):
    return f"""
        Dato il seguente contesto:
        [[[
        {context}
        ]]].
        Rispondi alla domanda dell'utente: [[[ {question} ]]].
        Spiega che nel file individuato c'e' il profilo piu' adatto.
        Assicurati di nominare il nome del file.
        Assicurati di indicare il nome del candidato: [[[ {candidate_name} ]]].
        Argomenta la scelta utilizzando il contenuto del testo individuato nel contesto.
        Se non trovi corrispondenza in nessun cv non inventare.
    """


@cl.on_chat_start
def on_chat_start():
    cl.user_session.set(
        "messages",
        [
            {
                "role": "system",
                "content": (
                    "Sei un assistente specializzato nel mondo HR. "
                    "Rispondi in modo professionale, sintetico e pragmatico. "
                    "Il tuo ruolo e' individuare il candidato ideale rispetto "
                    "alle richieste dell'utente."
                ),
            }
        ],
    )


@cl.on_message
async def handle_message(message: cl.Message):
    user_question = message.content

    try:
        cv_collection = get_collection()
        results = cv_collection.query(query_texts=[user_question], n_results=1)

        filename = results["metadatas"][0][0]["source"]
        candidate_intro = read_first_lines(DOCUMENTS_DIR / filename)
        candidate_name = get_candidate_name(candidate_intro)

        context = (
            f"CONTESTO: nome file {filename}; "
            f"paragrafo piu' significativo: {results['documents'][0][0]}"
        )
        prompt = create_prompt(context, user_question, candidate_name)

        messages = cl.user_session.get("messages", [])
        messages.append({"role": "user", "content": prompt})

        response_message = cl.Message(content="")
        await response_message.send()

        stream = ollama.chat(model=OLLAMA_MODEL, messages=messages, stream=True)

        for chunk in stream:
            await response_message.stream_token(chunk["message"]["content"])

        messages.append({"role": "assistant", "content": response_message.content})
        await response_message.update()
        cl.user_session.set("messages", messages)

    except Exception as error:
        await cl.Message(content=f"Errore: {error}").send()


@cl.on_chat_end
async def on_chat_end():
    await cl.Message(content="Grazie per aver utilizzato HR Assistant.").send()
