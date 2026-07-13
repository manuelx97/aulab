# flights_finder.py
import os
import json
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_classic.output_parsers import ResponseSchema, StructuredOutputParser
from serpapi import GoogleSearch
from pydantic import BaseModel, Field
from typing import Optional
from travel_agent_api.utils.tracing import trace_step

load_dotenv()


class FlightsInput(BaseModel):
    departure_airport: str = Field(description="Aeroporto di partenza in formato IATA, ad esempio FCO.")
    arrival_airport: str = Field(description="Aeroporto di arrivo in formato IATA, ad esempio CDG.")
    outbound_date: str = Field(description="Data del volo di andata nel formato YYYY-MM-DD.")
    return_date: str = Field(description="Data del volo di ritorno nel formato YYYY-MM-DD.")
    adults: Optional[int] = Field(1, description="Numero di passeggeri adulti.")
    children: Optional[int] = Field(0, description="Numero di passeggeri minorenni.")


class FlightsInputSchema(BaseModel):
    params: FlightsInput


response_schemas = [
    ResponseSchema(
        name="migliore_opzione",
        description=(
            "Sintesi markdown del volo piu' interessante, includendo compagnia, "
            "orari, durata, scali, prezzo e link quando disponibile."
        ),
    ),
    ResponseSchema(
        name="altre_opzioni",
        description=(
            "Massimo tre alternative utili, in markdown, ordinate per convenienza "
            "o qualita' complessiva."
        ),
    ),
]

output_parser = StructuredOutputParser.from_response_schemas(response_schemas)


@tool(args_schema=FlightsInputSchema)
def flights_finder(params: FlightsInput) -> dict:
    """
    Interroga Google Flights tramite SerpApi e trasforma la risposta in un riepilogo leggibile.

    Parameters:
        params (FlightsInput): aeroporti, date e passeggeri.

    Returns:
        dict: migliore opzione e alternative in formato strutturato.
    """
    try:
        search_params = {
            "api_key": os.getenv("SERPAPI_API_KEY"),
            "engine": "google_flights",
            "hl": "it",
            "gl": "it",
            "currency": "EUR",
            "stops": "1",
            "departure_id": params.departure_airport,
            "arrival_id": params.arrival_airport,
            "outbound_date": params.outbound_date,
            "return_date": params.return_date,
            "adults": params.adults,
            "children": params.children,
        }
        search = GoogleSearch(search_params)
        raw_results = search.get_dict()
        trace_step("flights_finder", "Risultati SerpApi ricevuti", list(raw_results.keys()))

        format_instructions = output_parser.get_format_instructions()
        model = ChatOpenAI(model_name="gpt-4o")
        response = model.invoke(
            f"Leggi questi dati SerpApi sui voli e prepara un riepilogo utile per un viaggiatore:\n"
            f"{json.dumps(raw_results, ensure_ascii=False)}\n\n{format_instructions}"
        )
        result = output_parser.parse(response.content)

        trace_step("flights_finder", "Sintesi voli generata", result)

        return result
    except Exception as e:
        trace_step("flights_finder", "Errore durante la ricerca voli", str(e))
        return str(e)
