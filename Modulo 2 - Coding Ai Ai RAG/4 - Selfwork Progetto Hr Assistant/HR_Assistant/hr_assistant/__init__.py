import chainlit as cl
from hr_assistant.config import Config
from hr_assistant.database import Database
from hr_assistant.document_processor import DocumentProcessor
from hr_assistant.utils import LLMHelper


db = None


def get_database():
    global db

    if db is None:
        db = Database()
        added, updated, removed = DocumentProcessor.process_documents(db)
        print(
            "Document sync complete: "
            f"{added} added, {updated} updated, {removed} removed"
        )

    return db


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
        database = get_database()
        results = database.query(user_question)

        filename = results["metadatas"][0][0]["source"]
        candidate_intro = DocumentProcessor.read_first_lines(
            Config.DOCUMENTS_DIR / filename,
            limit=100,
        )
        candidate_name = LLMHelper.get_candidate_name(candidate_intro)

        context = (
            f"CONTESTO: nome file {filename}; "
            f"paragrafo piu' significativo: {results['documents'][0][0]}"
        )
        prompt = LLMHelper.create_prompt(context, user_question, candidate_name)

        messages = cl.user_session.get("messages", [])
        messages.append({"role": "user", "content": prompt})

        response_message = cl.Message(content="")
        await response_message.send()

        stream = LLMHelper.chat(messages)

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
