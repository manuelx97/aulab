# Progetto Finale - Travel Agent API

Autore: Emanuel Marinelli  
Email: emanuelmarinelli@gmail.com  
GitHub: manuelx97

## Descrizione

Questo progetto rappresenta la parte backend del progetto finale della specializzazione Coding AI. L'applicazione espone una API FastAPI che usa LangChain, LangGraph e OpenAI per trasformare una richiesta di viaggio in una risposta organizzata: itinerario, voli, hotel, informazioni culturali e suggerimenti gastronomici.

Il frontend Laravel fornito nei materiali del corso puo' dialogare con questa API tramite l'endpoint `/chat/travel-agent`.

## Funzionalita principali

* assistente conversazionale dedicato alla pianificazione viaggi;
* generazione di itinerari giorno per giorno;
* ricerca voli tramite SerpApi e normalizzazione del risultato;
* ricerca hotel tramite SerpApi;
* risposte storico-culturali sulla destinazione;
* tool RAG per recuperare piatti tipici da Wikipedia e produrre un output validato;
* endpoint `/health` per controllare velocemente lo stato del servizio.

## Personalizzazioni

Rispetto alla base di partenza ho lavorato su alcuni aspetti specifici:

* ho aggiornato autore e contatti del progetto in `pyproject.toml`;
* ho riscritto questo README con una documentazione piu' aderente al mio lavoro;
* ho aggiunto un helper `trace_step` per rendere piu' chiari i log durante l'esecuzione;
* ho introdotto un endpoint `/health` con informazioni di servizio;
* ho corretto il nome del modello request in `ChatCompletionRequest`;
* ho riformulato prompt, descrizioni degli output e messaggi di tracing dell'agente;
* ho personalizzato lo User-Agent usato dal tool RAG nelle chiamate a Wikipedia.

## Struttura del progetto

```text
src/travel_agent_api/
├── main.py                  # configurazione FastAPI, CORS e health check
├── routes/
│   └── chat_router.py       # endpoint del travel agent
├── services/
│   └── agent_service.py     # orchestrazione LangGraph e output finale
├── tools/
│   ├── chain_historical_expert.py
│   ├── chain_travel_plan.py
│   ├── flights_finder.py
│   ├── hotels_finder.py
│   └── typical_dishes.py
└── utils/
    └── tracing.py           # utility per log e debugging
```

## Configurazione

Copiare il file `.env.example` in `.env` e valorizzare le chiavi:

```env
OPENAI_API_KEY="..."
SERPAPI_API_KEY="..."
```

La chiave OpenAI serve per il modello chat e gli embedding. La chiave SerpApi serve per i tool dedicati a voli e hotel.

## Avvio

Installazione con Poetry:

```bash
poetry install
```

Avvio della API:

```bash
poetry run uvicorn travel_agent_api.main:app --reload
```

La documentazione interattiva sara' disponibile su:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET /health
```

Endpoint principale:

```text
POST /chat/travel-agent
```

Esempio body:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Vorrei organizzare un viaggio di 4 giorni a Napoli con focus su cultura e cucina"
    }
  ]
}
```

## Come lavora l'agente

L'agente riceve la conversazione, aggiunge un system prompt con le istruzioni di formato e usa LangGraph per scegliere gli strumenti piu' adatti. La risposta finale viene poi ripulita tramite `StructuredOutputParser`, cosi' il frontend riceve un contenuto piu' ordinato e meno dispersivo.

I tool principali sono:

* `chain_travel_plan`, per costruire un itinerario coerente con date, budget e preferenze;
* `flights_finder`, per leggere i dati SerpApi dei voli e sintetizzarli;
* `hotels_finder`, per estrarre una selezione di hotel disponibili;
* `chain_historical_expert`, per domande culturali o storiche;
* `typical_dishes`, per cercare fonti Wikipedia, creare un vector store temporaneo e generare piatti tipici con output Pydantic.

## Tracing

Per seguire meglio il flusso dell'applicazione ho aggiunto stampe compatte con `trace_step`. I log permettono di vedere:

* quando arriva una richiesta;
* quando viene creato l'agente;
* quali tool sono disponibili;
* quanti messaggi produce LangGraph;
* se il parsing dell'output strutturato va a buon fine;
* quali step vengono eseguiti nella pipeline RAG.

## Note finali

Il progetto consegnato si concentra sulla parte Python richiesta dalla traccia. La parte Laravel resta il client web collegabile alla API, mentre questo backend contiene la logica principale di AI orchestration, tool calling, structured output e retrieval.
