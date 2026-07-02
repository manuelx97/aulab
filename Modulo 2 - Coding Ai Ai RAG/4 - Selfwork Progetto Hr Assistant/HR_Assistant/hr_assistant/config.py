import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    BASE_DIR = BASE_DIR
    DOCUMENTS_DIR = BASE_DIR / "resumes"
    COLLECTION_NAME = "CVs"
    PERSISTENT_DIR = BASE_DIR / "data" / "chromadb"

    EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    LOCAL_EMBEDDING_MODEL_PATH = BASE_DIR / "modelli" / "mio_modello"
    OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

    CHUNKING_VERSION = f"semantic-v1:{EMBEDDING_PROVIDER}:{EMBEDDING_MODEL}"
    SEMANTIC_BREAKPOINT_PERCENTILE = 95
    SEMANTIC_BUFFER_SIZE = 1
    OLLAMA_MODEL = "llama3.2"

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    @classmethod
    def require_openai_api_key(cls):
        if not cls.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY non trovata. Crea un file .env nella root del progetto."
            )

        return cls.OPENAI_API_KEY
