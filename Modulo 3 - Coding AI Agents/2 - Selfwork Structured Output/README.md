# Selfwork Structured Output

Esercizio con due esempi diversi di Structured Outputs:

1. Math tutor con modello Pydantic `MathReasoning`.
2. Riassunto di un articolo con modello Pydantic `ArticleSummary`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Poi inserisci la tua chiave OpenAI nel file `.env`.

## Avvio

```bash
python structured_outputs_examples.py
```
