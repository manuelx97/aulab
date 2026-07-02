from pathlib import Path
import shutil

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


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Ricerca candidato",
            message="Cercami un candidato che abbia le competenze di un saldatore",
            icon="/public/idea.svg",
        ),
    ]


@cl.on_chat_start
async def on_chat_start():
    actions = [
        cl.Action(
            name="db_stats",
            icon="database",
            payload={"value": "db_stats"},
            label="Statistiche Database",
        ),
        cl.Action(
            name="db_reindex",
            icon="refresh-cw",
            payload={"value": "db_reindex"},
            label="Reindex Database",
        ),
        cl.Action(
            name="db_remove",
            icon="trash-2",
            payload={"value": "db_remove"},
            label="Svuota completamente il Database",
        ),
    ]

    await cl.Message(content="Informazioni del sistema:", actions=actions).send()

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


@cl.action_callback("db_stats")
async def on_db_stats(action: cl.Action):
    database = get_database()
    db_info = database.get_stats()
    response = LLMHelper.get_db_stats(db_info)
    actions = [
        cl.Action(
            name="db_stats",
            icon="refresh-cw",
            payload={"value": "db_stats"},
            label="Ricalcola Statistiche Database",
        ),
    ]
    await cl.Message(content=response, actions=actions).send()


@cl.action_callback("db_reindex")
async def on_db_reindex(action: cl.Action):
    database = get_database()
    added, updated, removed = DocumentProcessor.process_documents(database)
    message = (
        "DB reindicizzato con successo. "
        f"Document sync complete: {added} added, {updated} updated, {removed} removed"
    )
    await cl.Message(content=message).send()


@cl.action_callback("db_remove")
async def on_db_remove(action: cl.Action):
    database = get_database()
    database.delete_collection()
    await cl.Message(
        content=(
            "Il database e' stato completamente rimosso. "
            "E' necessario lanciare il reindex o caricare nuovi file."
        )
    ).send()


async def process_and_index_file(file_path: Path, file_name: str):
    database = get_database()
    documents, metadatas, ids = DocumentProcessor.process_single_document(file_path)

    if documents:
        database.remove_document_by_source(file_name)
        database.add_documents(documents, metadatas, ids)
        return f"File '{file_name}' caricato e indicizzato con successo."

    return f"Errore nel processare il file '{file_name}'."


async def file_upload(file):
    Config.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    file_name = Path(file.name).name
    destination = Config.DOCUMENTS_DIR / file_name
    shutil.move(file.path, destination)

    return await process_and_index_file(destination, file_name)


async def handle_uploads(message: cl.Message):
    if not message.elements:
        return False

    supported_files = [
        file
        for file in message.elements
        if Path(file.name).suffix.lower() in DocumentProcessor.SUPPORTED_EXTENSIONS
    ]

    if not supported_files:
        await cl.Message(content="Nessun file supportato caricato.").send()
        return True

    await cl.Message(content="Caricamento e indicizzazione documenti").send()

    results = []
    for file in supported_files:
        results.append(await file_upload(file))

    await cl.Message(content="\n".join(results)).send()
    await cl.Message(content=f"Caricati {len(supported_files)} file").send()
    return True


@cl.on_message
async def handle_message(message: cl.Message):
    has_uploads = await handle_uploads(message)
    user_question = message.content.strip()

    if has_uploads and not user_question:
        return

    try:
        intent = LLMHelper.classify_intent(user_question)
        messages = cl.user_session.get("messages", [])

        if intent == "search_cv":
            database = get_database()
            results = database.query(user_question, n_results=3)

            if not results or not results["documents"] or not results["documents"][0]:
                await cl.Message(
                    content=(
                        "Nessun curriculum trovato per la richiesta. "
                        "Prova con competenze o ruolo piu' specifici."
                    )
                ).send()
                return

            filename = results["metadatas"][0][0]["source"]
            candidate_info = DocumentProcessor.read_first_lines(
                Config.DOCUMENTS_DIR / filename,
                limit=20,
            )

            context = (
                f"Nome file: {filename}\n"
                f"Estratto dal CV: {results['documents'][0][0]}"
            )
            cl.user_session.set("last_cv_context", context)
            cl.user_session.set("last_cv_header", candidate_info)

        else:
            context = cl.user_session.get("last_cv_context")
            candidate_info = cl.user_session.get("last_cv_header")

            if not context:
                await cl.Message(
                    content=(
                        "Non ho ancora un CV recente a cui fare riferimento. "
                        "Cerca prima un candidato, poi chiedimi dettagli sul suo profilo."
                    )
                ).send()
                return

        prompt = LLMHelper.create_prompt(
            context,
            user_question,
            candidate_info,
            intent=intent,
        )
        messages.append({"role": "user", "content": prompt})

        response_message = await stream_response(messages)
        messages.append({"role": "assistant", "content": response_message.content})
        cl.user_session.set("messages", messages)

    except Exception as error:
        await cl.Message(content=f"Errore: {error}").send()


async def stream_response(messages):
    response_message = cl.Message(content="")
    await response_message.send()

    stream = LLMHelper.chat(messages)
    for chunk in stream:
        await response_message.stream_token(chunk["message"]["content"])

    await response_message.update()
    return response_message


@cl.on_chat_end
async def on_chat_end():
    await cl.Message(content="Grazie per aver utilizzato HR Assistant.").send()
