from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langchain_classic.output_parsers import ResponseSchema, StructuredOutputParser
from langgraph.prebuilt import create_react_agent
# Tools
from travel_agent_api.tools.flights_finder import flights_finder
from travel_agent_api.tools.hotels_finder import hotels_finder
from travel_agent_api.tools.chain_historical_expert import chain_historical_expert
from travel_agent_api.tools.chain_travel_plan import chain_travel_plan
from travel_agent_api.tools.typical_dishes import typical_dishes
from travel_agent_api.utils.tracing import trace_step


response_schemas = [
    ResponseSchema(
        name="voli",
        description=(
            "Sezione markdown dedicata ai voli: evidenzia proposta migliore, "
            "orari, durata, scali, prezzo e link utile. Usa null quando la "
            "richiesta non prevede una ricerca voli."
        ),
    ),
    ResponseSchema(
        name="hotel",
        description=(
            "Sezione markdown dedicata agli alloggi: mostra nome struttura, "
            "zona o descrizione, prezzo, valutazione e servizi principali. "
            "Usa null se non sono stati cercati hotel."
        ),
    ),
    ResponseSchema(
        name="itinerario",
        description=(
            "Programma di viaggio in markdown, organizzato per giorno e per "
            "momenti della giornata. Usa null quando non viene richiesto un piano."
        ),
    ),
    ResponseSchema(
        name="risposta",
        description=(
            "Risposta libera in markdown per consigli, note pratiche o contenuti "
            "storico-culturali non coperti dalle altre sezioni. Usa null se non serve."
        ),
    ),
]

output_parser = StructuredOutputParser.from_response_schemas(response_schemas)


class Agent:
    def __init__(self):
        self.current_datetime = datetime.now()
        self.model = ChatOpenAI(model_name="gpt-4o")
        self.tools = [
            chain_historical_expert,
            flights_finder,
            hotels_finder,
            chain_travel_plan,
            typical_dishes,
        ]
        trace_step("Agent.__init__", "Agente inizializzato con i tool disponibili", [tool.name for tool in self.tools])
        self.agent_executor = create_react_agent(self.model, self.tools)

    def run(self, messages: list) -> list:
        trace_step("Agent.run", "Nuova conversazione presa in carico", messages)
        format_instructions = output_parser.get_format_instructions()

        SYSTEM_PROMPT = f"""
            Sei un consulente di viaggio digitale per utenti italiani.
            Aiuta l'utente a passare da un'idea generica a un piano concreto:
            itinerario, trasporti, hotel, contesto culturale e suggerimenti locali.
            Mantieni un tono pratico, ordinato e cordiale.
            Usa emoji con moderazione solo per rendere leggibili le sezioni.
            Quando mancano dati importanti, fai inferenze ragionevoli e dichiarale.
            La data di oggi è {self.current_datetime}.
            {format_instructions}
            """

        conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        response = self.agent_executor.invoke({"messages": conversation_history})

        all_messages = response["messages"][1:]
        trace_step("Agent.run", "Output grezzo ricevuto da LangGraph", len(all_messages))

        try:
            parsed = output_parser.parse(all_messages[-1].content)
            content = "\n\n".join(
                v.strip() for v in parsed.values()
                if v and v.strip().lower() not in ("null", "none", "")
            )
            all_messages = list(all_messages[:-1]) + [AIMessage(content=content)]
            trace_step("Agent.run", "Output finale normalizzato con StructuredOutputParser")
        except Exception as error:
            trace_step("Agent.run", "Parser non applicato: restituisco la risposta originale", str(error))

        return all_messages
