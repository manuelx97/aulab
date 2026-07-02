import chromadb

from hr_assistant.config import Config
from hr_assistant.custom_embedding import CustomEmbeddingFunction


class Database:
    def __init__(self):
        Config.PERSISTENT_DIR.mkdir(parents=True, exist_ok=True)

        self.embedding_function = CustomEmbeddingFunction()
        self.client = chromadb.PersistentClient(path=str(Config.PERSISTENT_DIR))
        self._init_collection()

    def _init_collection(self):
        self.collection = self.client.get_or_create_collection(
            name=Config.COLLECTION_NAME,
            embedding_function=self.embedding_function,
        )

    def delete_collection(self):
        try:
            self.client.delete_collection(Config.COLLECTION_NAME)
        except Exception:
            pass

        self._init_collection()

    def upsert_documents(self, documents, metadatas, ids):
        if not documents:
            raise RuntimeError("Nessun curriculum trovato nella cartella resumes.")

        self.collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

    def add_documents(self, documents, metadatas, ids):
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )

    def query(self, query_text, n_results=1):
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
        )

    def get_tracked_files(self):
        result = self.collection.get()
        tracked_files = {}

        if result and result["metadatas"]:
            for metadata in result["metadatas"]:
                source = metadata.get("source")
                if source and source not in tracked_files:
                    tracked_files[source] = {
                        "hash": metadata.get("hash"),
                        "last_modified": metadata.get("last_modified"),
                        "source": source,
                    }

        return tracked_files

    def remove_document_by_source(self, source):
        result = self.collection.get(where={"source": source})
        if result and result["ids"]:
            self.collection.delete(ids=result["ids"])

    def get_stats(self):
        result = self.collection.get()
        metadatas = result.get("metadatas") or []
        sources = {metadata["source"] for metadata in metadatas if metadata.get("source")}

        return (
            f"Nome collezione: {self.collection.name}\n"
            f"Numero totale frammenti: {self.collection.count()}\n"
            f"Numero file elaborati: {len(sources)}"
        )
