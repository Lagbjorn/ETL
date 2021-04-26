import random
from tqdm import tqdm

from django.db import transaction
from django.core.management.base import BaseCommand

from movies.models import (
    FilmWork,
    FilmWorkPerson,
    FilmWorkGenre,
    Person,
    Genre
)
from movies.factories import (
    FilmWorkFactory,
    PersonFactory,
    GenreFactory,
    FilmWorkGenreFactory,
    FilmWorkPersonFactory,
)

NUM_PERSONS = 5_000
NUM_FILMS = 1_000
NUM_GENRES = 10
GENRES_PER_FILM = 5
PERSONS_PER_FILM = 20


class Command(BaseCommand):
    help = 'Create fake data for tests'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Removing old data...')
        models = [FilmWork, FilmWorkPerson, FilmWorkGenre, Person, Genre]
        for model in models:
            self.stdout.write(f'Removing {model.__name__} objects...')
            model.objects.all().delete()

        # use generator because NUM_FILMS is LARGE and I want my RAM to stay alive
        films = (FilmWorkFactory() for _ in range(NUM_FILMS))
        # use list comprehensions because these are smaller
        # & I want to sample from the entire set of these
        persons = [PersonFactory() for _ in tqdm(range(NUM_PERSONS), desc='Creating persons')]
        genres = [GenreFactory() for _ in tqdm(range(NUM_GENRES), desc='Creating genres')]

        for film in tqdm(films, desc="Creating fake FilmWorks", total=NUM_FILMS):
            # sample first to avoid duplicates
            persons_sample = random.sample(persons, random.randint(0, PERSONS_PER_FILM))
            genres_sample = random.sample(genres, random.randint(0, GENRES_PER_FILM))

            for genre in genres_sample:
                filmworkgenre = FilmWorkGenreFactory(genre=genre, film_work=film)
            for person in persons_sample:
                filmworkperson = FilmWorkPersonFactory(person=person, film_work=film)
