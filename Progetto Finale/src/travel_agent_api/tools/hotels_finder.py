# hotels_finder.py
import os
import json
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_classic.output_parsers import ResponseSchema, StructuredOutputParser
from serpapi import GoogleSearch
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional
from enum import IntEnum
from travel_agent_api.utils.tracing import trace_step

load_dotenv()


class HotelClassEnum(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5


class HotelsInput(BaseModel):
    q: str = Field(description="Destinazione o zona in cui cercare l'alloggio.")
    check_in_date: str = Field(description="Data di check-in nel formato YYYY-MM-DD.")
    check_out_date: str = Field(description="Data di check-out nel formato YYYY-MM-DD.")
    adults: Optional[int] = Field(1, description="Numero di ospiti adulti.")
    children: Optional[int] = Field(0, description="Numero di bambini presenti.")
    children_ages: Optional[str] = Field("", description="Eta' dei bambini separate da virgola, se disponibili.")
    hotel_class: Optional[int] = Field(2, description="Categoria minima o desiderata dell'hotel, da 2 a 5 stelle.")


class HotelsInputSchema(BaseModel):
    params: HotelsInput


response_schemas = [
    ResponseSchema(
        name="hotel",
        description=(
            "Selezione markdown di massimo cinque hotel con nome, fascia prezzo, "
            "valutazione, servizi rilevanti e note utili per scegliere."
        ),
    ),
]

output_parser = StructuredOutputParser.from_response_schemas(response_schemas)


@tool(args_schema=HotelsInputSchema)
def hotels_finder(params: HotelsInput) -> dict:
    """
    Cerca hotel tramite SerpApi e restituisce una selezione sintetica e confrontabile.

    Parameters:
        params (HotelsInput): destinazione, date, ospiti e categoria desiderata.

    Returns:
        dict: lista hotel sintetizzata nella chiave hotel.
    """
    search_params = {
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "engine": "google_hotels",
        "hl": "it",
        "gl": "it",
        "currency": "EUR",
        "q": params.q,
        "check_in_date": params.check_in_date,
        "check_out_date": params.check_out_date,
        "adults": params.adults,
        "children": params.children,
        "children_ages": params.children_ages,
        "hotel_class": params.hotel_class,
        "num": 5,
    }

    try:
        search = GoogleSearch(search_params)
        raw_results = search.get_dict()
        trace_step("hotels_finder", "Risultati SerpApi ricevuti", list(raw_results.keys()))

        format_instructions = output_parser.get_format_instructions()
        model = ChatOpenAI(model_name="gpt-4o")
        response = model.invoke(
            f"Analizza questi dati SerpApi sugli hotel e crea una selezione chiara per l'utente:\n"
            f"{json.dumps(raw_results, ensure_ascii=False)}\n\n{format_instructions}"
        )
        result = output_parser.parse(response.content)

        trace_step("hotels_finder", "Sintesi hotel generata", result)

        return result
    except Exception as e:
        trace_step("hotels_finder", "Errore durante la ricerca hotel", str(e))
        return str(e)
