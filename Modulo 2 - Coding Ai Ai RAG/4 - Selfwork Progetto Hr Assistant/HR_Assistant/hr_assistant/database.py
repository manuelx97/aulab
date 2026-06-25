import chromadb
from chromadb.utils import embedding_functions

from hr_assistant.config import Config


class Database:
    def __init__(self):
        Config.PERSISTENT_DIR.mkdir(parents=True, exist_ok=True)

        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=Config.require_openai_api_key(),
            model_name=Config.EMBEDDING_MODEL,
        )

        self.client = chromadb.PersistentClient(path=str(Config.PERSISTENT_DIR))
        self.collection = self.client.get_or_create_collection(
            name=Config.COLLECTION_NAME,
            embedding_function=openai_ef,
        )

    def upsert_documents(self, documents, metadatas, ids):
        if not documents:
            raise RuntimeError("Nessun curriculum trovato nella cartella resumes.")

        self.collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

    def query(self, query_text, n_results=1):
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
        )
