# HR Assistant

Progetto unico Poetry per il selfwork HR Assistant.

## Avanzamento 3

In questo avanzamento il progetto contiene una app Chainlit con una versione RAG organizzata in moduli:

- legge i curriculum nella cartella `resumes`;
- divide i testi in chunk;
- crea embedding OpenAI e li inserisce in ChromaDB persistente;
- cerca il chunk piu' vicino alla richiesta dell'utente;
- usa Ollama per estrarre il nome del candidato;
- usa Ollama in streaming per generare la risposta HR.

La logica e' divisa in:

- `config.py`: configurazioni e caricamento `.env`;
- `document_processor.py`: lettura CV e chunking;
- `database.py`: ChromaDB persistente;
- `utils.py`: chiamate a Ollama e costruzione prompt;
- `__init__.py`: app Chainlit.

## Setup

```bash
poetry install
```

Imposta la chiave OpenAI per gli embedding creando un file `.env` non tracciato da Git:

```bash
OPENAI_API_KEY="la-tua-api-key"
```

Il file deve trovarsi nella root del progetto `HR_Assistant`.

Il database Chroma viene creato in `data/chromadb`, cartella ignorata da Git.

Avvia Ollama e scarica il modello usato dalla chat:

```bash
ollama run llama3.2
```

## Avvio

```bash
poetry run chainlit run app.py -w
```

Se usi la venv classica:

```bash
chainlit run app.py -w
```
