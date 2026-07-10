from __future__ import annotations

import os
from pathlib import Path
from textwrap import dedent

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL = "gpt-4o"


class MathReasoning(BaseModel):
    class Step(BaseModel):
        explanation: str
        output: str

    steps: list[Step]
    final_answer: str


class ArticleSummary(BaseModel):
    class Concept(BaseModel):
        title: str
        description: str

    invented_year: int
    summary: str
    inventors: list[str]
    description: str
    concepts: list[Concept]


def build_client() -> OpenAI:
    load_dotenv(BASE_DIR / ".env")

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY mancante. Crea un file .env partendo da .env.example."
        )

    return OpenAI()


def solve_math_problem(client: OpenAI, question: str) -> MathReasoning:
    math_tutor_prompt = dedent(
        """
        Sei un tutor di matematica.
        Riceverai un problema matematico e dovrai restituire una soluzione
        passo dopo passo, con una spiegazione e l'equazione prodotta a ogni step.
        """
    )

    completion = client.beta.chat.completions.parse(
        model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        messages=[
            {"role": "system", "content": math_tutor_prompt},
            {"role": "user", "content": question},
        ],
        response_format=MathReasoning,
    )

    message = completion.choices[0].message
    if message.refusal:
        raise RuntimeError(f"Richiesta rifiutata dal modello: {message.refusal}")

    return message.parsed


def summarize_article(client: OpenAI, article_path: Path) -> ArticleSummary:
    summarization_prompt = dedent(
        """
        Ti verra fornito il contenuto di un articolo su una tecnologia AI.
        Riassumilo seguendo lo schema richiesto:
        - invented_year: anno di invenzione o pubblicazione principale
        - summary: riassunto in una frase
        - inventors: nomi degli inventori/autori citati, se presenti
        - concepts: concetti chiave con titolo e descrizione
        - description: breve descrizione generale
        """
    )

    completion = client.beta.chat.completions.parse(
        model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        temperature=0.2,
        messages=[
            {"role": "system", "content": summarization_prompt},
            {"role": "user", "content": article_path.read_text(encoding="utf-8")},
        ],
        response_format=ArticleSummary,
    )

    message = completion.choices[0].message
    if message.refusal:
        raise RuntimeError(f"Richiesta rifiutata dal modello: {message.refusal}")

    return message.parsed


def print_math_result(result: MathReasoning) -> None:
    print("\nESEMPIO 1 - Math tutor structured output")
    print("-" * 50)
    for index, step in enumerate(result.steps, start=1):
        print(f"Step {index}")
        print(f"Spiegazione: {step.explanation}")
        print(f"Output: {step.output}\n")
    print(f"Risposta finale: {result.final_answer}")


def print_article_summary(summary: ArticleSummary) -> None:
    print("\nESEMPIO 2 - Article summary structured output")
    print("-" * 50)
    print(f"Anno: {summary.invented_year}")
    print(f"Riassunto: {summary.summary}")
    print("\nInventori/autori:")
    for inventor in summary.inventors:
        print(f"- {inventor}")
    print("\nConcetti:")
    for concept in summary.concepts:
        print(f"- {concept.title}: {concept.description}")
    print(f"\nDescrizione: {summary.description}")


def main() -> None:
    client = build_client()

    math_result = solve_math_problem(client, "Risolvi 8x + 7 = -23")
    print_math_result(math_result)

    article_path = BASE_DIR / "structured_outputs_articles" / "llms.md"
    article_summary = summarize_article(client, article_path)
    print_article_summary(article_summary)


if __name__ == "__main__":
    main()
