# Selfwork FastAPI

Autore: Emanuel Marinelli  
Email: emanuelmarinelli@gmail.com  
GitHub: manuelx97

## Descrizione

Questo esercizio del Modulo 4 contiene una piccola API realizzata con FastAPI. Il tema scelto e' una libreria: gli endpoint permettono di leggere, filtrare, creare, aggiornare ed eliminare libri.

L'obiettivo del selfwork e' mostrare i concetti principali visti nella lezione:

* creazione di una app FastAPI;
* path parameters;
* query parameters;
* enum;
* validazioni con Pydantic;
* request body;
* response model;
* gestione degli errori con `HTTPException`;
* documentazione automatica tramite Swagger UI.

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

In alternativa:

```bash
python -m uvicorn src.fastapi_ex.main:app --reload
```

## Documentazione API

Dopo l'avvio, aprire:

```text
http://127.0.0.1:8000/docs
```

## Endpoint principali

```text
GET     /
GET     /health
GET     /genres/{genre}
GET     /files/{file_path:path}
GET     /books
GET     /books/{book_id}
GET     /authors/{author_id}/books/{book_id}
POST    /books
PUT     /books/{book_id}
PATCH   /books/{book_id}
DELETE  /books/{book_id}
```

## Esempi

Lista libri con filtri:

```text
GET /books?genre=tech&in_stock=true&limit=5&offset=0
```

Dettaglio libro:

```text
GET /books/1
```

Creazione libro:

```json
{
  "title": "Designing Data-Intensive Applications",
  "author": "Martin Kleppmann",
  "genre": "tech",
  "price": 42.5,
  "pages": 616,
  "in_stock": true,
  "description": "Libro tecnico su sistemi distribuiti e architetture dati."
}
```

Aggiornamento parziale:

```json
{
  "price": 39.9,
  "in_stock": false
}
```

## Note

Il database e' simulato con una lista Python in memoria. Questo mantiene il progetto semplice e focalizzato sui concetti FastAPI richiesti dall'esercizio.
