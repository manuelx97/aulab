# Selfwork FastAPI

Autore: Emanuel Marinelli  
Email: emanuelmarinelli@gmail.com  
GitHub: manuelx97

## Descrizione

Questo selfwork replica l'esercizio FastAPI visto nella lezione. Il progetto mostra gli esempi principali per creare una API con:

* path parameters;
* enum nei path parameters;
* path converter per percorsi file;
* query parameters;
* request body con Pydantic;
* validazioni con `Field`;
* uso di `Annotated` e `Query`;
* documentazione automatica tramite `/docs`.

Ho mantenuto la struttura dell'esercizio originale, aggiungendo solo una documentazione piu' completa, i miei metadati e una piccola variazione sul path dell'esempio con query parameters (`/items/query/{item_id}`) per evitare sovrapposizioni con l'endpoint `/items/{item_id}`.

## Installazione

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Avvio

```bash
uvicorn src.fastapi_ex.main:app --reload
```

In alternativa, usando Poetry:

```bash
poetry run uvicorn src.fastapi_ex.main:app --reload
```

## Documentazione

Dopo l'avvio, la documentazione interattiva e' disponibile qui:

```text
http://127.0.0.1:8000/docs
```

## Endpoint presenti

```text
GET  /
GET  /items/{item_id}
GET  /models/{model_name}
GET  /files/{file_path:path}
GET  /items/
GET  /items/query/{item_id}
POST /items/
PUT  /items/{item_id}
GET  /items/get
```

## Esempi rapidi

Path parameter:

```text
GET /items/10
```

Enum nel path:

```text
GET /models/alexnet
GET /models/resnet
GET /models/lenet
```

Query parameters:

```text
GET /items/?skip=0&limit=2
GET /items/query/test?q=ciao&short=true
```

Body Pydantic:

```json
{
  "name": "Notebook",
  "description": "Quaderno per appunti",
  "price": 12.5,
  "tax": 2.5
}
```
