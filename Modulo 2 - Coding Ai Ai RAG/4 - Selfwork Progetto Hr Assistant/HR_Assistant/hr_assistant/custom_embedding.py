import ollama
from chromadb.api.types import EmbeddingFunction
from chromadb.utils import embedding_functions

from hr_assistant.config import Config


class CustomEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self.provider = Config.EMBEDDING_PROVIDER
        self.model_name = Config.EMBEDDING_MODEL
        self.model_path = Config.LOCAL_EMBEDDING_MODEL_PATH

        if self.provider == "openai":
            self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=Config.require_openai_api_key(),
                model_name=self.model_name,
            )
        elif self.provider == "local":
            self.embedding_function = self._load_local_model()
        elif self.provider == "ollama":
            self.embedding_function = None
        else:
            raise ValueError(
                f"EMBEDDING_PROVIDER '{self.provider}' non supportato. "
                "Usa openai, local oppure ollama."
            )

    def __call__(self, input):
        texts = list(input)

        if self.provider == "openai":
            return self.embedding_function(texts)

        if self.provider == "local":
            return self.embedding_function.encode(texts).tolist()

        return [
            ollama.embeddings(model=Config.OLLAMA_EMBEDDING_MODEL, prompt=text)[
                "embedding"
            ]
            for text in texts
        ]

    def _load_local_model(self):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise RuntimeError(
                "Per usare EMBEDDING_PROVIDER=local installa sentence-transformers."
            ) from error

        if self.model_path.exists():
            return SentenceTransformer(str(self.model_path))

        model = SentenceTransformer(self.model_name)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(str(self.model_path))
        return model
