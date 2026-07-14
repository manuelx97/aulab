from enum import Enum
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Query, status
from pydantic import BaseModel, Field


app = FastAPI(
    title="Selfwork FastAPI - Bookstore",
    description=(
        "Esercizio FastAPI del Modulo 4. "
        "API dimostrativa per gestire una piccola libreria."
    ),
    version="1.0.0",
)


class Genre(str, Enum):
    fantasy = "fantasy"
    thriller = "thriller"
    classic = "classic"
    tech = "tech"
    travel = "travel"


class Book(BaseModel):
    id: int
    title: str
    author: str
    genre: Genre
    price: float = Field(..., gt=0)
    pages: int = Field(..., gt=0)
    in_stock: bool = True
    description: str | None = Field(default=None, max_length=300)


class BookCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=120)
    author: str = Field(..., min_length=2, max_length=80)
    genre: Genre
    price: float = Field(..., gt=0, description="Book price in EUR.")
    pages: int = Field(..., gt=0, le=3000)
    in_stock: bool = True
    description: str | None = Field(default=None, max_length=300)


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=120)
    author: str | None = Field(default=None, min_length=2, max_length=80)
    genre: Genre | None = None
    price: float | None = Field(default=None, gt=0)
    pages: int | None = Field(default=None, gt=0, le=3000)
    in_stock: bool | None = None
    description: str | None = Field(default=None, max_length=300)


class BookFilters(BaseModel):
    limit: int = Field(default=10, gt=0, le=50)
    offset: int = Field(default=0, ge=0)
    genre: Genre | None = None
    in_stock: bool | None = None


books_db: list[Book] = [
    Book(
        id=1,
        title="Il nome della rosa",
        author="Umberto Eco",
        genre=Genre.classic,
        price=14.90,
        pages=536,
        in_stock=True,
        description="Romanzo storico e investigativo ambientato in un monastero medievale.",
    ),
    Book(
        id=2,
        title="Clean Code",
        author="Robert C. Martin",
        genre=Genre.tech,
        price=38.50,
        pages=464,
        in_stock=True,
        description="Libro di riferimento per scrivere codice piu' leggibile e manutenibile.",
    ),
    Book(
        id=3,
        title="In Patagonia",
        author="Bruce Chatwin",
        genre=Genre.travel,
        price=12.00,
        pages=272,
        in_stock=False,
        description="Racconto di viaggio tra luoghi, incontri e memorie della Patagonia.",
    ),
]


def find_book(book_id: int) -> Book:
    for book in books_db:
        if book.id == book_id:
            return book
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Book with id {book_id} not found.",
    )


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Selfwork FastAPI completato",
        "author": "Emanuel Marinelli",
        "github": "manuelx97",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "bookstore-api"}


@app.get("/genres/{genre}")
async def read_genre(genre: Genre) -> dict[str, str]:
    return {
        "genre": genre,
        "message": f"Books filtered by {genre.value} genre.",
    }


@app.get("/files/{file_path:path}")
async def read_file_path(file_path: str) -> dict[str, str]:
    return {"file_path": file_path}


@app.get("/books", response_model=list[Book])
async def list_books(filters: Annotated[BookFilters, Query()]) -> list[Book]:
    filtered_books = books_db

    if filters.genre is not None:
        filtered_books = [book for book in filtered_books if book.genre == filters.genre]

    if filters.in_stock is not None:
        filtered_books = [
            book for book in filtered_books if book.in_stock == filters.in_stock
        ]

    return filtered_books[filters.offset : filters.offset + filters.limit]


@app.get("/books/{book_id}", response_model=Book)
async def read_book(
    book_id: Annotated[int, Path(gt=0, description="Book identifier.")],
    include_description: bool = Query(default=True),
) -> Book:
    book = find_book(book_id)
    if include_description:
        return book

    return book.model_copy(update={"description": None})


@app.get("/authors/{author_id}/books/{book_id}")
async def read_author_book(
    author_id: Annotated[int, Path(gt=0)],
    book_id: Annotated[int, Path(gt=0)],
) -> dict[str, int | Book]:
    return {
        "author_id": author_id,
        "book": find_book(book_id),
    }


@app.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
async def create_book(book: BookCreate) -> Book:
    new_id = max(book.id for book in books_db) + 1 if books_db else 1
    new_book = Book(id=new_id, **book.model_dump())
    books_db.append(new_book)
    return new_book


@app.put("/books/{book_id}", response_model=Book)
async def replace_book(
    book_id: Annotated[int, Path(gt=0)],
    book: BookCreate,
) -> Book:
    stored_book = find_book(book_id)
    updated_book = Book(id=stored_book.id, **book.model_dump())

    book_index = books_db.index(stored_book)
    books_db[book_index] = updated_book
    return updated_book


@app.patch("/books/{book_id}", response_model=Book)
async def update_book(
    book_id: Annotated[int, Path(gt=0)],
    book_update: BookUpdate,
) -> Book:
    stored_book = find_book(book_id)
    update_data = book_update.model_dump(exclude_unset=True)
    updated_book = stored_book.model_copy(update=update_data)

    book_index = books_db.index(stored_book)
    books_db[book_index] = updated_book
    return updated_book


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: Annotated[int, Path(gt=0)]) -> None:
    stored_book = find_book(book_id)
    books_db.remove(stored_book)
