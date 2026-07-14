from enum import Enum
from typing import Annotated

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field


app = FastAPI(
    title="Selfwork FastAPI",
    description="Esercizio base su path params, query params e request body.",
    version="1.0.0",
)


@app.get("/")
async def root():
    return {
        "message": "Ciao Mondo",
        "author": "Emanuel Marinelli",
        "github": "manuelx97",
    }


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}
    return {"model_name": model_name, "message": "Have some residuals"}


@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}


fake_items_db = [
    {"item_name": "Foo"},
    {"item_name": "Bar"},
    {"item_name": "Baz"},
]


@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]


@app.get("/items/query/{item_id}")
async def read_item_with_query(
    item_id: str,
    q: str | None = None,
    short: bool = False,
):
    item = {"item_id": item_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update({"description": "This is a detailed description of the item."})
    return item


class Item(BaseModel):
    name: str
    description: str | None = Field(
        None,
        title="Descrizione dell'elemento",
        max_length=300,
    )
    price: float = Field(
        ...,
        gt=0,
        description="Il prezzo dell'elemento, deve essere maggiore di zero",
    )
    tax: float | None = None


@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.model_dump()
    if item.tax:
        item_dict.update({"price_with_tax": item.price + item.tax})
    return item_dict


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, q: str | None = None):
    result = {"item_id": item_id, **item.model_dump()}
    if q:
        result.update({"q": q})
    return result


class FilterParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: str = "created_at"
    tags: list[str] = []


@app.get("/items/get")
async def read_items_get(filter_query: Annotated[FilterParams, Query()]):
    return filter_query


@app.get("/items/{item_id}")
async def read_item_by_id(item_id: int):
    return {"item_id": item_id}
