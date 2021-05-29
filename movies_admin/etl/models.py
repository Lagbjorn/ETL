from typing import List, Optional

from pydantic import BaseModel


class FilmWorkES(BaseModel):
    id: str
    title: str
    imdb_rating: Optional[float]
    genre: List[str]
    writers_names: List[str]
    actors_names: List[str]
    director: List[str]
    description: str
