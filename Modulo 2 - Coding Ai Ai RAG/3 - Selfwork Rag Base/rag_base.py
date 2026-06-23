from pathlib import Path
import os

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from openai import OpenAI


DOCUMENTS_DIR = Path("resumes")
COLLECTION_NAME = "CVs"
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"


def load_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY non trovata. Copia .env.example in .env e inserisci la tua chiave."
        )
    return api_key


def load_documents(documents_dir: Path):
    documents = []
    metadatas = []
    ids = []

    current_id = 0

    for file_path in sorted(documents_dir.glob("*.txt")):
        text = file_path.read_text(encoding="utf-8")
        chunks = [
            chunk.strip()
            for chunk in text.replace("\n", ". ").split("### ")
            if chunk.strip()
        ]

        if not chunks:
            continue

        candidate_info = chunks[0]

        for chunk in chunks:
            documents.append(chunk)
            metadatas.append(
                {
                    "source": file_path.name,
                    "info": candidate_info,
                }
            )
            ids.append(str(current_id))
            current_id += 1

    return documents, metadatas, ids


def build_collection(api_key: str, documents, metadatas, ids):
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name=EMBEDDING_MODEL,
    )

    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=openai_ef,
    )

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )

    return collection


def retrieve_context(collection, user_question: str):
    results = collection.query(
        query_texts=[user_question],
        n_results=1,
    )

    metadata = results["metadatas"][0][0]
    document = results["documents"][0][0]

    return (
        "CONTESTO: "
        f"nome file {metadata['source']}; "
        f"paragrafo piu' significativo: {document}; "
        "ricorda sempre di menzionare il nome del candidato all'inizio "
        "e i dati personali alla fine per il contatto. "
        f"Dati personali: {metadata['info']}"
    )


def generate_answer(api_key: str, user_question: str, context: str) -> str:
    prompt = f"""Dato il seguente contesto:
{context}

Rispondi alla domanda dell'utente:
{user_question}

Spiega che nel file individuato c'e' il profilo piu' adatto.
Argomenta la scelta utilizzando il contenuto del testo individuato nel contesto.
"""

    client = OpenAI(api_key=api_key)

    completion = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "Sei un assistente HR, specializzato nella ricerca di profili professionali.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
    )

    return completion.choices[0].message.content


def main():
    api_key = load_api_key()
    documents, metadatas, ids = load_documents(DOCUMENTS_DIR)

    if not documents:
        raise RuntimeError("Nessun documento trovato nella cartella resumes.")

    collection = build_collection(api_key, documents, metadatas, ids)

    user_question = "mi serve qualcuno per promuovere il mio prodotto"
    context = retrieve_context(collection, user_question)
    answer = generate_answer(api_key, user_question, context)

    print(answer)


if __name__ == "__main__":
    main()
