# HR Assistant

Progetto unico Poetry per il selfwork HR Assistant.

## Avanzamento 2

In questo avanzamento il progetto contiene una app Chainlit con una prima versione RAG:

- legge i curriculum nella cartella `resumes`;
- divide i testi in chunk;
- crea embedding OpenAI e li inserisce in ChromaDB;
- cerca il chunk piu' vicino alla richiesta dell'utente;
- usa Ollama per estrarre il nome del candidato;
- usa Ollama in streaming per generare la risposta HR.

## Setup

```bash
poetry install
```

Imposta la chiave OpenAI per gli embedding creando un file `.env` non tracciato da Git:

```bash
OPENAI_API_KEY="la-tua-api-key"
```

Il file deve trovarsi nella root del progetto `HR_Assistant`.

Avvia Ollama e scarica il modello usato dalla chat:

```bash
ollama run llama3.2
```

## Avvio

```bash
poetry run chainlit run hr_assistant/__init__.py -w
```
