# main.py
from fastapi import FastAPI
from travel_agent_api.routes import chat_router
from fastapi.middleware.cors import CORSMiddleware
from travel_agent_api.utils.tracing import trace_step

app = FastAPI(
    title="Travel Agent API",
    description="API FastAPI e LangChain per il progetto finale Coding AI.",
    version="1.0.0",
)

origins = [
    "http://127.0.0.1:8000",  # Porta standard Laravel front-end
    "http://localhost:8000",   # Alias localhost Laravel front-end
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    chat_router.router,
    tags=["Chat"],
    prefix="/chat",
)


@app.get("/health", tags=["Health"])
def health_check():
    trace_step("health_check", "API health check requested")
    return {
        "status": "ok",
        "service": "travel-agent-api",
        "author": "Emanuel Marinelli",
        "github": "manuelx97",
    }
