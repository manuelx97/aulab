from __future__ import annotations

import json
from typing import Optional


class BookInfoTool:
    def __init__(self) -> None:
        self.books = {
            "il_nome_della_rosa": {
                "title": "Il nome della rosa",
                "author": "Umberto Eco",
                "genre": "mistero storico",
                "audience": "adulti",
                "description": "Un'indagine medievale tra filosofia, potere e conoscenza.",
                "price": 14.90,
                "available_copies": 3,
            },
            "harry_potter_e_la_pietra_filosofale": {
                "title": "Harry Potter e la pietra filosofale",
                "author": "J.K. Rowling",
                "genre": "fantasy",
                "audience": "ragazzi",
                "description": "L'inizio della saga fantasy ambientata a Hogwarts.",
                "price": 12.50,
                "available_copies": 5,
            },
            "dune": {
                "title": "Dune",
                "author": "Frank Herbert",
                "genre": "fantascienza",
                "audience": "adulti",
                "description": "Un classico della fantascienza su politica, ecologia e destino.",
                "price": 16.00,
                "available_copies": 2,
            },
            "la_casa_sul_mare_celeste": {
                "title": "La casa sul mare celeste",
                "author": "T.J. Klune",
                "genre": "fantasy",
                "audience": "young adult",
                "description": "Una storia tenera e luminosa su diversita, cura e famiglia scelta.",
                "price": 15.20,
                "available_copies": 0,
            },
            "atomic_habits": {
                "title": "Atomic Habits",
                "author": "James Clear",
                "genre": "crescita personale",
                "audience": "adulti",
                "description": "Metodo pratico per costruire abitudini migliori in piccoli passi.",
                "price": 18.00,
                "available_copies": 4,
            },
        }

    @staticmethod
    def _normalize(value: str) -> str:
        return value.lower().strip().replace(" ", "_")

    def get_info(self, title: str) -> str:
        book = self.books.get(self._normalize(title))
        if not book:
            available_titles = ", ".join(book["title"] for book in self.books.values())
            return f"Libro non trovato. Titoli disponibili: {available_titles}"

        status = "disponibile" if book["available_copies"] > 0 else "non disponibile"
        return (
            f"Titolo: {book['title']}\n"
            f"Autore: {book['author']}\n"
            f"Genere: {book['genre']}\n"
            f"Pubblico: {book['audience']}\n"
            f"Descrizione: {book['description']}\n"
            f"Prezzo: euro {book['price']:.2f}\n"
            f"Stato: {status}, copie disponibili: {book['available_copies']}"
        )

    def search_books(
        self,
        genre: Optional[str] = None,
        audience: Optional[str] = None,
        available_only: bool = False,
    ) -> str:
        results = list(self.books.values())

        if genre:
            results = [book for book in results if genre.lower() in book["genre"].lower()]

        if audience:
            results = [
                book for book in results if audience.lower() in book["audience"].lower()
            ]

        if available_only:
            results = [book for book in results if book["available_copies"] > 0]

        if not results:
            return "Nessun libro trovato con i filtri richiesti."

        payload = [
            {
                "title": book["title"],
                "author": book["author"],
                "genre": book["genre"],
                "audience": book["audience"],
                "available_copies": book["available_copies"],
            }
            for book in results
        ]
        return json.dumps(payload, ensure_ascii=False)


class LibraryEventTool:
    def __init__(self) -> None:
        self.events = [
            {
                "name": "Club del libro fantasy",
                "topic": "Fantasy e young adult",
                "date": "2026-07-16",
                "time": "18:30",
                "spots_available": 10,
            },
            {
                "name": "Incontro su Umberto Eco",
                "topic": "Mistero storico e semiotica",
                "date": "2026-07-22",
                "time": "19:00",
                "spots_available": 6,
            },
            {
                "name": "Serata fantascienza",
                "topic": "Dune e mondi possibili",
                "date": "2026-08-04",
                "time": "18:00",
                "spots_available": 12,
            },
            {
                "name": "Laboratorio abitudini di lettura",
                "topic": "Crescita personale",
                "date": "2026-08-20",
                "time": "17:30",
                "spots_available": 8,
            },
        ]

    def get_events(
        self,
        topic: Optional[str] = None,
        start_date: Optional[str] = None,
    ) -> str:
        filtered_events = self.events

        if topic:
            filtered_events = [
                event for event in filtered_events if topic.lower() in event["topic"].lower()
            ]

        if start_date:
            filtered_events = [
                event for event in filtered_events if event["date"] >= start_date
            ]

        if not filtered_events:
            return f"Nessun evento trovato. Eventi disponibili: {self.events}"

        result = "Eventi disponibili:\n"
        for event in filtered_events:
            result += (
                f"- {event['name']} ({event['topic']}): {event['date']} "
                f"alle {event['time']}, posti disponibili: {event['spots_available']}\n"
            )
        return result


class ReservationTool:
    def __init__(self, book_tool: BookInfoTool) -> None:
        self.book_tool = book_tool

    def reserve_book(self, title: str, customer_name: str, pickup_date: str) -> str:
        book_key = self.book_tool._normalize(title)
        book = self.book_tool.books.get(book_key)

        if not book:
            return self.book_tool.get_info(title)

        if book["available_copies"] <= 0:
            return (
                f"Mi dispiace, '{book['title']}' non e disponibile al momento. "
                "Posso suggerire un libro simile o segnalarti quando torna disponibile."
            )

        book["available_copies"] -= 1
        return (
            f"Prenotazione confermata per {customer_name}.\n"
            f"Libro: {book['title']} di {book['author']}\n"
            f"Ritiro previsto: {pickup_date}\n"
            f"Codice prenotazione: LIB-{book_key[:6].upper()}-{pickup_date.replace('-', '')}"
        )
