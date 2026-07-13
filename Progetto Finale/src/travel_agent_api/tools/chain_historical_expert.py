# chain_historical_expert.py
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.output_parsers import ResponseSchema, StructuredOutputParser
from travel_agent_api.utils.tracing import trace_step


response_schemas = [
    ResponseSchema(
        name="answer",
        description="Spiegazione storico-culturale chiara, contestualizzata e adatta a un viaggiatore.",
    ),
    ResponseSchema(
        name="key_facts",
        description="Punti essenziali da ricordare, in forma sintetica.",
    ),
    ResponseSchema(
        name="further_reading",
        description="Suggerimenti di approfondimento, come luoghi, musei, libri o fonti.",
    ),
]

output_parser = StructuredOutputParser.from_response_schemas(response_schemas)


@tool
def chain_historical_expert(input_text: str) -> dict:
    """
    Produce una risposta culturale utile per arricchire il viaggio dell'utente.

    Args:
        input_text (str): argomento storico, artistico o culturale richiesto.

    Returns:
        dict: contenuto strutturato con spiegazione, punti chiave e approfondimenti.
    """
    model = ChatOpenAI(model_name="gpt-4o")

    system_prompt = """
    Sei una guida culturale con taglio divulgativo.
    Spiega il tema richiesto in modo preciso ma comprensibile, collegandolo
    quando possibile all'esperienza concreta di viaggio: luoghi da vedere,
    contesto storico, curiosita' utili e cosa osservare sul posto.
    """

    format_instructions = output_parser.get_format_instructions()

    prompt = ChatPromptTemplate([
        ("system", "{system_prompt}"),
        ("user", "{format_instructions}\n\n{input}"),
    ])

    chain = prompt | model

    response = chain.invoke({
        "input": input_text,
        "system_prompt": system_prompt,
        "format_instructions": format_instructions,
    })
    result = output_parser.parse(response.content)

    trace_step("chain_historical_expert", "Risposta culturale generata", result)

    return result
