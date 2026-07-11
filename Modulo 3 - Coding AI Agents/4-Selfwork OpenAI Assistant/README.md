# Selfwork OpenAI Assistant

Replica del progetto OpenAI Assistant visto nella video-lezione, adattata a un assistente per una piccola agenzia viaggi: **TravelMate**.

Il progetto usa:

- OpenAI Assistants API;
- `file_search` su una knowledge base locale;
- una funzione custom `request_travel_quote`;
- Chainlit come interfaccia chat.

Nota: l'Assistants API e' oggi nella sezione legacy/migration della documentazione OpenAI, ma qui viene usata per replicare la traccia della video-lezione.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Inserisci la tua `OPENAI_API_KEY` nel file `.env`.

## Crea l'assistant

Da lanciare una sola volta:

```bash
python travel_assistant/create_assistant.py
```

Copia l'`Assistant ID` stampato nel file `.env`:

```env
ASSISTANT_ID=asst_...
```

## Avvio app

```bash
chainlit run travel_assistant/__init__.py -w
```

## Prompt di esempio

```text
Vorrei un viaggio di 7 giorni in Giappone per due persone, budget medio.
```

```text
Quali documenti servono per il pacchetto Islanda?
```

```text
Mi prepari un preventivo per Parigi a settembre? Mi chiamo Emanuel Marinelli e la mia email e emanuelmarinelli@gmail.com
```
