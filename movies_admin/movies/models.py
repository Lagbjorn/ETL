import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel


class FilmWorkType(models.TextChoices):
    TV_SHOW = 'tv_show', _('шоу')
    MOVIE = 'movie', _('фильм')
    SERIES = 'series', _('сериал')


class PersonJob(models.TextChoices):
    ACTOR = 'actor', _('актёр')
    DIRECTOR = 'director', _('режиссёр')
    WRITER = 'writer', _('сценарист')


class Person(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()

    class Meta:
        db_table = 'person'
        verbose_name = _('человек')
        verbose_name_plural = _('люди')

    def __str__(self):
        return self.name


class Genre(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    genre = models.CharField(_('жанр'), max_length=255)

    class Meta:
        db_table = 'genre'
        verbose_name = _('жанр')
        verbose_name_plural = _('жанры')

    def __str__(self):
        return self.genre


class FilmWork(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    creation_date = models.DateField(blank=True, null=True)
    film_rating = models.CharField(blank=True,
                                   null=True,
                                   max_length=32,
                                   help_text='suitability for different age audience')
    imdb_rating = models.FloatField(blank=True,
                                    null=True,
                                    help_text='user ratings from IMDb')
    genres = models.ManyToManyField(Genre, through='FilmWorkGenre')
    persons = models.ManyToManyField(Person, through='FilmWorkPerson')
    film_type = models.CharField(_('тип'), max_length=32, choices=FilmWorkType.choices, blank=True, null=True)

    class Meta:
        db_table = 'film_work'
        verbose_name = _('кинопроизведение')
        verbose_name_plural = _('кинопроизведения')

    def __str__(self):
        return self.title


class FilmWorkGenre(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    film_work = models.ForeignKey(FilmWork, models.DO_NOTHING)
    genre = models.ForeignKey(Genre, models.DO_NOTHING)

    class Meta:
        db_table = 'film_work_genre'


class FilmWorkPerson(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    film_work = models.ForeignKey(FilmWork, models.DO_NOTHING)
    person = models.ForeignKey(Person, models.DO_NOTHING)
    job = models.CharField(_('должность'), max_length=32, choices=PersonJob.choices)

    class Meta:
        db_table = 'film_work_person'