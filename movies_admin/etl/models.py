from typing import List, Optional

from pydantic import BaseModel


class BasePerson(BaseModel):
    id: str
    full_name: str


class BaseGenre(BaseModel):
    id: str
    name: str


class FilmWorkES(BaseModel):
    id: str
    title: str
    description: str
    rating: Optional[float]
    genres: List[BaseGenre]
    genres_names: List[str]
    writers_names: List[str]
    actors_names: List[str]
    directors_names: List[str]
    writers: List[BasePerson]
    actors: List[BasePerson]
    directors: List[BasePerson]
