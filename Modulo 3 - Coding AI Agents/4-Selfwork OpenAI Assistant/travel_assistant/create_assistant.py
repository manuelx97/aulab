from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent.parent
KB_DIR = BASE_DIR / "kb"

load_dotenv(BASE_DIR / ".env")

OPENAI_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_KEY:
    raise RuntimeError("OPENAI_API_KEY mancante. Crea un file .env da .env.example.")

client = OpenAI(api_key=OPENAI_KEY)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "request_travel_quote",
            "description": "Registra una richiesta di preventivo viaggio quando l'utente fornisce i dati necessari.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nome e cognome del cliente.",
                    },
                    "email": {
                        "type": "string",
                        "description": "Email del cliente.",
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destinazione o pacchetto richiesto.",
                    },
                    "period": {
                        "type": "string",
                        "description": "Periodo indicativo del viaggio.",
                    },
                    "travelers": {
                        "type": "integer",
                        "description": "Numero di viaggiatori.",
                    },
                    "budget": {
                        "type": "string",
                        "description": "Budget indicativo del cliente.",
                    },
                },
                "required": ["name", "email", "destination", "period", "travelers"],
            },
        },
    },
    {"type": "file_search"},
]


def create_new_assistant():
    assistant = client.beta.assistants.create(
        name="TravelMate Assistant",
        instructions="""
Il tuo nome e TravelMate.
Sei l'assistente virtuale di una piccola agenzia viaggi.
Usa la knowledge base collegata per rispondere su pacchetti, prezzi indicativi,
documenti, pagamenti, modifiche e cancellazioni.

Quando l'utente chiede un preventivo personalizzato, raccogli almeno:
nome, email, destinazione, periodo, numero viaggiatori e budget se disponibile.
Quando hai i dati necessari, chiama la funzione request_travel_quote.

Non inventare prezzi o condizioni non presenti nei file: se un dettaglio manca,
spiega che serve conferma da un consulente TravelMate.
""",
        tools=TOOLS,
        model=MODEL,
    )

    vector_store = client.beta.vector_stores.create(name="TravelMate Knowledge Base")

    file_paths = [KB_DIR / "packages.txt", KB_DIR / "policies.txt"]
    file_streams = [path.open("rb") for path in file_paths]

    try:
        client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            files=file_streams,
        )
    finally:
        for file_stream in file_streams:
            file_stream.close()

    assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
    )

    return assistant


if __name__ == "__main__":
    assistant = create_new_assistant()
    print("\nAssistant ID:", assistant.id)
    print("Copia questo valore nel file .env come ASSISTANT_ID.\n")
