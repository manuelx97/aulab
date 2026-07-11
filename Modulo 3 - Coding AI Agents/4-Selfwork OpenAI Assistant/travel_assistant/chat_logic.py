from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent.parent
OUTBOX_DIR = BASE_DIR / "outbox"


@dataclass
class QuoteRequest:
    name: str
    email: str
    destination: str
    period: str
    travelers: int
    budget: Optional[str] = None


class ChatLogic:
    def __init__(self, openai_key: str, assistant_id: str):
        if not openai_key:
            raise RuntimeError("OPENAI_API_KEY mancante nel file .env.")
        if not assistant_id:
            raise RuntimeError("ASSISTANT_ID mancante. Esegui prima create_assistant.py.")

        self.client = OpenAI(api_key=openai_key)
        self.assistant_id = assistant_id
        self.thread_id = None

    def initialize_thread(self) -> str:
        if not self.thread_id:
            thread = self.client.beta.threads.create()
            self.thread_id = thread.id
        return self.thread_id

    def request_travel_quote(
        self,
        name: str,
        email: str,
        destination: str,
        period: str,
        travelers: int,
        budget: Optional[str] = None,
    ) -> str:
        quote = QuoteRequest(
            name=name,
            email=email,
            destination=destination,
            period=period,
            travelers=travelers,
            budget=budget,
        )

        OUTBOX_DIR.mkdir(exist_ok=True)
        file_name = f"quote_{quote.email.replace('@', '_at_').replace('.', '_')}.json"
        (OUTBOX_DIR / file_name).write_text(
            json.dumps(quote.__dict__, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return (
            "Richiesta di preventivo registrata correttamente. "
            "Un consulente TravelMate rispondera entro 2 giorni lavorativi."
        )

    def handle_function_calls(self, run, thread_id: str):
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        tool_outputs = []

        for tool in tool_calls:
            function_name = tool.function.name
            function_args = json.loads(tool.function.arguments or "{}")

            if function_name == "request_travel_quote":
                output = self.request_travel_quote(**function_args)
            else:
                output = f"Funzione non riconosciuta: {function_name}"

            tool_outputs.append({"tool_call_id": tool.id, "output": output})

        if tool_outputs:
            return self.client.beta.threads.runs.submit_tool_outputs_and_poll(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs,
            )

        return run

    def process_message(self, user_message: str) -> Optional[str]:
        thread_id = self.initialize_thread()

        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message,
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=self.assistant_id,
        )

        while run.status != "completed":
            if run.status == "requires_action":
                run = self.handle_function_calls(run, thread_id)
                continue

            if run.status in {"failed", "cancelled", "expired"}:
                return f"Run terminato con stato: {run.status}"

            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id,
            )

        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        for message in messages.data:
            if message.run_id == run.id and message.role == "assistant":
                return message.content[0].text.value

        return "Non ho trovato una risposta dell'assistente."
