import chainlit as cl


@cl.on_chat_start
async def on_chat_start():
    await cl.Message(
        content="Ciao, sono HR Assistant. Scrivimi un messaggio per iniziare."
    ).send()


@cl.on_message
async def handle_message(message: cl.Message):
    response = f"Ciao, mi hai scritto: {message.content}!"
    await cl.Message(content=response).send()
