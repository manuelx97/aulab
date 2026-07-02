import os
from pathlib import Path

from dotenv import load_dotenv


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DOCUMENTS_DIR = BASE_DIR / "resumes"
    COLLECTION_NAME = "CVs"
    PERSISTENT_DIR = BASE_DIR / "data" / "chromadb"

    EMBEDDING_MODEL = "text-embedding-3-small"
    CHUNKING_VERSION = "semantic-v1"
    OLLAMA_MODEL = "llama3.2"

    load_dotenv(BASE_DIR / ".env")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    @classmethod
    def require_openai_api_key(cls):
        if not cls.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY non trovata. Crea un file .env nella root del progetto."
            )

        return cls.OPENAI_API_KEY
