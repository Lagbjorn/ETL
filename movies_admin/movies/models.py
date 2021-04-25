import uuid

from django.db import models
from model_utils.models import TimeStampedModel


class Person(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.TextField()

    class Meta:
        db_table = 'person'


class Genre(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    genre = models.TextField()

    class Meta:
        db_table = 'genre'


class FilmWork(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.TextField()
    description = models.TextField(blank=True, null=True)
    imdb_rating = models.FloatField(blank=True, null=True)
    genres = models.ManyToManyField(Genre, through='FilmWorkGenre', through_fields=('film_work', 'genre', ))

    class Meta:
        db_table = 'film_work'


class FilmWorkGenre(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    film_work = models.ForeignKey(FilmWork, models.DO_NOTHING)
    genre = models.ForeignKey('Genre', models.DO_NOTHING)

    class Meta:
        db_table = 'film_work_genre'


class FilmWorkPerson(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    film_work = models.ForeignKey(FilmWork, models.DO_NOTHING)
    person = models.ForeignKey('Person', models.DO_NOTHING)
    job = models.TextField()  # This field type is a guess.

    class Meta:
        db_table = 'film_work_person'
