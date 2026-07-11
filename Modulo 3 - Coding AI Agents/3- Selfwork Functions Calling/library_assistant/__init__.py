from __future__ import annotations

import json
import os
from datetime import datetime

import chainlit as cl
from dotenv import load_dotenv
from openai import OpenAI

try:
    from library_assistant.tools import BookInfoTool, LibraryEventTool, ReservationTool
except ModuleNotFoundError:
    from tools import BookInfoTool, LibraryEventTool, ReservationTool


load_dotenv()

book_tool = BookInfoTool()
event_tool = LibraryEventTool()
reservation_tool = ReservationTool(book_tool)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_book_info",
            "description": "Ottiene informazioni su un libro specifico della libreria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Titolo del libro richiesto.",
                    }
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_books",
            "description": "Cerca libri filtrando per genere, pubblico e disponibilita.",
            "parameters": {
                "type": "object",
                "properties": {
                    "genre": {
                        "type": "string",
                        "description": "Genere del libro, ad esempio fantasy o fantascienza.",
                    },
                    "audience": {
                        "type": "string",
                        "description": "Pubblico consigliato, ad esempio ragazzi, young adult o adulti.",
                    },
                    "available_only": {
                        "type": "boolean",
                        "description": "True se l'utente vuole solo libri disponibili.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_events",
            "description": "Ottiene eventi, presentazioni e club di lettura in programma.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Tema dell'evento, ad esempio fantasy o crescita personale.",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Data minima in formato YYYY-MM-DD.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reserve_book",
            "description": "Prenota un libro disponibile per il ritiro in libreria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Titolo del libro da prenotare.",
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Nome e cognome del cliente.",
                    },
                    "pickup_date": {
                        "type": "string",
                        "description": "Data di ritiro desiderata in formato YYYY-MM-DD.",
                    },
                },
                "required": ["title", "customer_name", "pickup_date"],
            },
        },
    },
]


def build_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY mancante. Crea un file .env partendo da .env.example."
        )
    return OpenAI(api_key=api_key)


def handle_tool_call(tool_call) -> str:
    function_args = json.loads(tool_call.function.arguments or "{}")
    function_name = tool_call.function.name

    print("*" * 80)
    print("function name:", function_name)
    print("function args:", function_args)
    print("*" * 80)

    if function_name == "get_book_info":
        result = book_tool.get_info(**function_args)
    elif function_name == "search_books":
        result = book_tool.search_books(**function_args)
    elif function_name == "get_upcoming_events":
        result = event_tool.get_events(**function_args)
    elif function_name == "reserve_book":
        result = reservation_tool.reserve_book(**function_args)
    else:
        result = f"Funzione non riconosciuta: {function_name}"

    print("result:", result)
    print("*" * 80)
    return result


def llm(messages):
    client = build_client()
    return client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )


@cl.on_chat_start
def on_chat_start():
    today = datetime.today().strftime("%Y-%m-%d")
    cl.user_session.set(
        "messages",
        [
            {
                "role": "developer",
                "content": (
                    "Sei un assistente della libreria indipendente Libreria Marinelli. "
                    "Aiuti gli utenti a trovare libri, conoscere eventi e prenotare "
                    f"copie per il ritiro. Oggi e' il {today}. "
                    "Quando hai bisogno di dati di catalogo usa gli strumenti disponibili."
                ),
            }
        ],
    )


@cl.on_message
async def main(message: cl.Message):
    messages = cl.user_session.get("messages")
    messages.append({"role": "user", "content": message.content})

    try:
        while True:
            completion = llm(messages)
            response_message = completion.choices[0].message
            tool_calls = response_message.tool_calls

            if response_message.refusal:
                messages.append(response_message)
                break

            if response_message.content:
                messages.append(response_message)
                break

            if tool_calls:
                messages.append(response_message)

                for tool_call in tool_calls:
                    function_response = handle_tool_call(tool_call)
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": tool_call.function.name,
                            "content": function_response,
                        }
                    )
            else:
                messages.append(
                    {
                        "role": "assistant",
                        "content": "Non sono riuscito a generare una risposta. Riprova.",
                    }
                )
                break
    except RuntimeError as error:
        messages.append({"role": "assistant", "content": str(error)})

    cl.user_session.set("messages", messages)
    await cl.Message(author="assistant", content=messages[-1].content).send()
