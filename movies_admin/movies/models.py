import uuid
from datetime import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

# This datetime must be definitely older than the project
# datetime.min is not used because it raises django OVERFLOW error when using timedelta
DATETIME_ANCIENT = datetime(year=2020, month=1, day=1, hour=0, minute=0)


class FilmWorkType(models.TextChoices):
    """Available film work types"""
    TV_SHOW = 'tv_show', _('шоу')
    MOVIE = 'movie', _('фильм')
    SERIES = 'series', _('сериал')


class PersonJob(models.TextChoices):
    """Available person jobs"""
    ACTOR = 'actor', _('актёр')
    DIRECTOR = 'director', _('режиссёр')
    WRITER = 'writer', _('сценарист')


class Person(TimeStampedModel):
    """Person who has participated in film work creation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(_('имя'))

    class Meta:
        db_table = 'person'
        verbose_name = _('человек')
        verbose_name_plural = _('люди')
        indexes = (
            models.Index(fields=('name', )),
        )

    def __str__(self):
        return self.name


class Genre(TimeStampedModel):
    """Genres available for film works"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    genre = models.CharField(_('жанр'), max_length=255, unique=True)
    description = models.TextField(_('описание'), blank=True, default='')

    class Meta:
        db_table = 'genre'
        verbose_name = _('жанр')
        verbose_name_plural = _('жанры')
        indexes = (
            models.Index(fields=('genre', )),
        )

    def __str__(self):
        return self.genre


class FilmWork(TimeStampedModel):
    """Film work of some kind: movie, tv show, series"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('название'), max_length=255)
    description = models.TextField(_('описание'), blank=True, default='')
    creation_date = models.DateField(_('дата выхода'), blank=True, null=True)
    film_rating = models.CharField(_('возрастной рейтинг'), blank=True,
                                   max_length=32,
                                   default='',
                                   help_text='suitability for different age audience')
    imdb_rating = models.FloatField(_('IMDb рейтинг'), blank=True,
                                    null=True,
                                    help_text='user ratings from IMDb')
    genres = models.ManyToManyField(Genre, through='FilmWorkGenre')
    persons = models.ManyToManyField(Person, through='FilmWorkPerson')
    film_type = models.CharField(_('тип'), max_length=32, choices=FilmWorkType.choices, blank=True, default='')

    # ElasticSearch specific field
    indexed_at = models.DateTimeField(_('дата индексации в ElasticSearch'), default=DATETIME_ANCIENT)

    class Meta:
        db_table = 'film_work'
        verbose_name = _('кинопроизведение')
        verbose_name_plural = _('кинопроизведения')
        indexes = (
            models.Index(fields=('title',)),
            models.Index(fields=('creation_date',)),
        )

    def __str__(self):
        return self.title


class FilmWorkGenre(TimeStampedModel):
    """M2M relation between film work and genre"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    film_work = models.ForeignKey(FilmWork, models.DO_NOTHING)
    genre = models.ForeignKey(Genre, models.DO_NOTHING)

    class Meta:
        db_table = 'film_work_genre'
        indexes = (
            models.Index(fields=('film_work', 'genre', )),
        )


class FilmWorkPerson(TimeStampedModel):
    """
    M2M relation between film work and person. Additionally holds
    information about person's job in a film work
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    film_work = models.ForeignKey(FilmWork, models.DO_NOTHING)
    person = models.ForeignKey(Person, models.DO_NOTHING)
    job = models.CharField(_('должность'), max_length=32, choices=PersonJob.choices)

    class Meta:
        db_table = 'film_work_person'
        indexes = (
            models.Index(fields=('film_work', 'person', )),
        )
