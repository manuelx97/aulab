# chain_travel_plan.py
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.output_parsers import ResponseSchema, StructuredOutputParser
from pydantic import BaseModel, Field
from typing import Optional
from travel_agent_api.utils.tracing import trace_step


class TravelPlanInput(BaseModel):
    start_date: str = Field(description="Giorno di partenza nel formato YYYY-MM-DD.")
    end_date: str = Field(description="Giorno di rientro nel formato YYYY-MM-DD.")
    destination: str = Field(description="Citta' o area geografica da visitare.")
    adults: Optional[int] = Field(1, description="Viaggiatori adulti inclusi nella richiesta.")
    children: Optional[int] = Field(0, description="Eventuali bambini presenti nel gruppo.")
    travel_style: str = Field(description="Taglio del viaggio: cultura, relax, famiglia, natura, lusso, low cost.")
    budget: Optional[int] = Field(description="Budget complessivo disponibile in euro.")
    activities: str = Field(description="Interessi principali indicati dall'utente.")
    food_restriction: str = Field(description="Vincoli alimentari o preferenze da rispettare.")


class TravelPlanInputSchema(BaseModel):
    params: TravelPlanInput


response_schemas = [
    ResponseSchema(
        name="travel_plan",
        description=(
            "Itinerario in markdown diviso per giornate, con attivita' consigliate "
            "al mattino, al pomeriggio e alla sera."
        ),
    ),
]

output_parser = StructuredOutputParser.from_response_schemas(response_schemas)


@tool(args_schema=TravelPlanInputSchema)
def chain_travel_plan(params: TravelPlanInput) -> dict:
    """
    Genera un itinerario pratico e leggibile a partire dalle preferenze dell'utente.

    Parameters:
        params (TravelPlanInput): date, destinazione, composizione del gruppo,
        budget, stile di viaggio, interessi e restrizioni alimentari.

    Returns:
        dict: itinerario strutturato nella chiave travel_plan.
    """
    model = ChatOpenAI(model_name="gpt-4o")

    system_prompt = f"""
    Agisci come travel designer per un utente italiano.
    Costruisci un programma realistico, evitando giornate troppo cariche.
    Inserisci suggerimenti concreti e compatibili con preferenze e budget.

    Dati viaggio:
    - partenza: {params.start_date}
    - rientro: {params.end_date}
    - destinazione: {params.destination}
    - adulti: {params.adults}
    - bambini: {params.children}
    - stile: {params.travel_style}
    - budget: {params.budget} EUR
    - interessi: {params.activities}
    - restrizioni alimentari: {params.food_restriction}
    """

    format_instructions = output_parser.get_format_instructions()

    prompt = ChatPromptTemplate([("human", "{input}\n\n{format_instructions}")])
    chain = prompt | model
    response = chain.invoke({"input": system_prompt, "format_instructions": format_instructions})
    result = output_parser.parse(response.content)

    trace_step("chain_travel_plan", "Itinerario generato", result)

    return result
