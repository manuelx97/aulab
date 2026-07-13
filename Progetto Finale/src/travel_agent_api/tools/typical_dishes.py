# typical_dishes.py
from typing import List
import requests
from langchain_core.tools import tool
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from travel_agent_api.utils.tracing import trace_step

WIKIPEDIA_HEADERS = {"User-Agent": "travel-agent-api/1.0 (Emanuel Marinelli; manuelx97)"}


def _fetch_wikipedia_docs(query: str, lang: str = "it", max_pages: int = 3) -> list[Document]:
    """Recupera pagine Wikipedia con requests e le converte in Document LangChain."""
    base_url = f"https://{lang}.wikipedia.org/w/api.php"

    # Cerca i titoli più pertinenti per la query gastronomica.
    search_resp = requests.get(base_url, headers=WIKIPEDIA_HEADERS, timeout=10, params={
        "action": "query", "list": "search",
        "srsearch": query, "srlimit": max_pages, "format": "json",
    })
    search_resp.raise_for_status()
    titles = [r["title"] for r in search_resp.json()["query"]["search"]]
    trace_step("typical_dishes.wikipedia", f"Pagine trovate su Wikipedia {lang}", titles)

    # Scarica il contenuto testuale delle pagine individuate.
    docs = []
    for title in titles:
        content_resp = requests.get(base_url, headers=WIKIPEDIA_HEADERS, timeout=10, params={
            "action": "query", "prop": "extracts", "explaintext": True,
            "titles": title, "format": "json", "exsectionformat": "plain",
        })
        content_resp.raise_for_status()
        pages = content_resp.json()["query"]["pages"]
        for page in pages.values():
            text = page.get("extract", "")
            if text:
                docs.append(Document(page_content=text[:15000], metadata={"title": title, "lang": lang}))

    return docs

# Cache in-memory: evita di re-indicizzare città già processate
_vector_stores: dict[str, Chroma] = {}


class Dish(BaseModel):
    name: str = Field(description="Nome del piatto o prodotto tipico.")
    description: str = Field(description="Descrizione breve, utile per un turista.")
    category: str = Field(description="Categoria gastronomica: primo, secondo, dolce, street food, bevanda o prodotto locale.")


class TypicalDishesOutput(BaseModel):
    city: str = Field(description="Destinazione gastronomica analizzata.")
    dishes: List[Dish] = Field(description="Proposte tipiche da provare durante il viaggio.")


def _build_vector_store(city: str) -> Chroma:
    """Costruisce un vector store temporaneo partendo da contenuti Wikipedia."""
    trace_step("typical_dishes.rag", "Avvio costruzione vector store", city)

    query = f"cucina {city}"
    trace_step("typical_dishes.rag", "Query Wikipedia preparata", query)
    docs = []
    for lang in ["it", "en"]:
        try:
            docs = _fetch_wikipedia_docs(query, lang=lang, max_pages=3)
            trace_step("typical_dishes.rag", f"Documenti caricati in lingua {lang}", len(docs))
            if docs:
                break
        except Exception as e:
            trace_step("typical_dishes.rag", f"Recupero Wikipedia {lang} non riuscito", str(e))

    if not docs:
        return None
    for i, doc in enumerate(docs):
        trace_step(
            "typical_dishes.rag",
            f"Documento {i + 1} pronto",
            {"title": doc.metadata.get("title", "N/A"), "chars": len(doc.page_content)},
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(docs)
    trace_step("typical_dishes.rag", "Chunk creati per la ricerca semantica", len(chunks))
    for i, chunk in enumerate(chunks[:3]):
        trace_step(
            "typical_dishes.rag",
            f"Anteprima chunk {i + 1}",
            chunk.page_content[:80],
        )

    trace_step("typical_dishes.rag", "Creazione embedding OpenAI text-embedding-3-small")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vector_store = Chroma.from_documents(chunks, embeddings)
    trace_step("typical_dishes.rag", "Vector store Chroma creato", len(chunks))

    return vector_store


@tool
def typical_dishes(city: str) -> TypicalDishesOutput:
    """
    Usa una pipeline RAG per proporre piatti tipici collegati alla citta' richiesta.

    Args:
        city (str): destinazione per cui recuperare suggerimenti gastronomici.

    Returns:
        TypicalDishesOutput: lista validata di piatti o prodotti tipici.
    """
    trace_step("typical_dishes", "Richiesta gastronomica ricevuta", city)

    if city not in _vector_stores:
        trace_step("typical_dishes", "Destinazione non in cache: indicizzazione necessaria", city)
        vector_store = _build_vector_store(city)
        if vector_store is None:
            trace_step("typical_dishes", "Nessun documento disponibile: restituisco output vuoto", city)
            return TypicalDishesOutput(city=city, dishes=[])
        _vector_stores[city] = vector_store
    else:
        trace_step("typical_dishes", "Destinazione gia' presente in cache", city)

    vector_store = _vector_stores[city]

    query = f"piatti primi secondi dolci street food ricette {city}"
    trace_step("typical_dishes", "Query di retrieval preparata", query)
    retrieved_docs = vector_store.similarity_search(query, k=8)
    trace_step("typical_dishes", "Chunk recuperati dalla similarity search", len(retrieved_docs))
    for i, doc in enumerate(retrieved_docs):
        trace_step("typical_dishes", f"Chunk recuperato {i + 1}", doc.page_content[:100])

    context = "\n\n".join(doc.page_content for doc in retrieved_docs)

    trace_step("typical_dishes", "Generazione output strutturato con gpt-4o")
    model = ChatOpenAI(model_name="gpt-4o")
    output_parser = PydanticOutputParser(pydantic_object=TypicalDishesOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "Sei un consulente gastronomico per viaggiatori. "
            "Usa il contesto come fonte principale e seleziona piatti, prodotti o dolci "
            "che una persona dovrebbe provare nella citta' indicata. "
            "Se il contesto e' scarso, integra con conoscenza generale, mantenendo "
            "la risposta concreta e verificabile. Restituisci almeno 5 proposte.\n\n"
            "Contesto:\n{context}\n\n"
            "Formato output:\n{format_instructions}"
        )),
        ("human", "Prepara una lista di specialita' gastronomiche per {city}."),
    ])

    chain = prompt | model | output_parser
    result = chain.invoke({
        "city": city,
        "context": context,
        "format_instructions": output_parser.get_format_instructions(),
    })

    trace_step("typical_dishes", "Numero di proposte gastronomiche estratte", len(result.dishes))
    for dish in result.dishes:
        trace_step("typical_dishes", f"{dish.category} - {dish.name}", dish.description[:80])

    return result
