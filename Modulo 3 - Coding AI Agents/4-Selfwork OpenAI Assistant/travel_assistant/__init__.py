from __future__ import annotations

import os
from pathlib import Path

import chainlit as cl
from dotenv import load_dotenv

try:
    from travel_assistant.chat_logic import ChatLogic
except ModuleNotFoundError:
    from chat_logic import ChatLogic


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@cl.on_chat_start
def on_chat_start():
    cl.user_session.set(
        "chat_logic",
        ChatLogic(
            openai_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY"),
            assistant_id=os.getenv("ASSISTANT_ID"),
        ),
    )


@cl.on_message
async def main(message: cl.Message):
    chat_logic = cl.user_session.get("chat_logic")
    response = chat_logic.process_message(message.content)

    await cl.Message(
        author="assistant",
        content=response,
    ).send()
