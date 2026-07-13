from fastapi import APIRouter
from pydantic import BaseModel
from travel_agent_api.services.agent_service import Agent
from travel_agent_api.utils.tracing import trace_step

router = APIRouter()


# Payload atteso dal client Laravel o dalla pagina /docs di FastAPI.
class ChatCompletionRequest(BaseModel):
    messages: list
    model_config = {
        "json_schema_extra": {
            "example": {
                "messages": [
                    {
                        "role": "user",
                        "content": "Organizzami un weekend a Torino tra musei, buon cibo e hotel centrale"
                    }
                ]
            }
        }
    }


@router.post("/travel-agent")  # Definizione dell'endpoint POST per il travel agent
def chat_completion(request: ChatCompletionRequest):
    """
    Riceve la cronologia chat e delega la richiesta all'agente di viaggio.

    Args:
    request (ChatCompletionRequest): messaggi della conversazione nel formato role/content.

    Returns:
    list: messaggi prodotti dall'agente e dai tool LangChain/LangGraph.
    """
    trace_step("chat_completion", "Messaggi ricevuti dal client", request.messages)
    agent = Agent()
    response = agent.run(messages=request.messages)
    trace_step("chat_completion", "Risposta pronta per il client", response)
    return response
