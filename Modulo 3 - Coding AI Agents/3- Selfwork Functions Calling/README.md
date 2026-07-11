# Selfwork Functions Calling

Replica del progetto visto nella video-lezione, adattata a un assistente per una libreria.

L'assistente puo usare tre funzioni:

- `get_book_info`: recupera informazioni su un libro.
- `get_upcoming_events`: cerca eventi, presentazioni e club di lettura.
- `reserve_book`: prenota un libro per il ritiro in libreria.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Inserisci la tua chiave OpenAI nel file `.env`.

## Avvio

```bash
chainlit run library_assistant/__init__.py -w
```

## Esempi di prompt

```text
Vorrei un fantasy disponibile per un ragazzo di 14 anni.
```

```text
Hai eventi di lettura dopo il 2026-07-15?
```

```text
Prenotami Il nome della rosa per Emanuel Marinelli il 2026-07-12.
```
