import uuid
from dataclasses import dataclass


@dataclass
class FilmWork:
    id: uuid.UUID
    title: str
    description: str
    imdb_rating: float


@dataclass
class Person:
    id: uuid.UUID
    name: str


@dataclass
class Genre:
    id: uuid.UUID
    genre: str
