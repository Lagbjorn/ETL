import factory
from factory.django import DjangoModelFactory

from .models import FilmWork, Person, Genre, FilmWorkPerson, FilmWorkGenre, FilmWorkType, PersonJob


class FilmWorkFactory(DjangoModelFactory):
    class Meta:
        model = FilmWork

    title = factory.Faker(
        'sentence',
        nb_words=6,
        variable_nb_words=True
    )
    description = factory.Faker(
        'sentence',
        nb_words=128,
        variable_nb_words=True
    )
    creation_date = factory.Faker('date')
    film_rating = factory.Faker('word')
    imdb_rating = factory.Faker('pyfloat', min_value=0, max_value=10, right_digits=1)
    film_type = factory.Faker('word', ext_word_list=FilmWorkType.values)


class PersonFactory(DjangoModelFactory):
    class Meta:
        model = Person

    name = factory.Faker("name")


class FilmWorkPersonFactory(DjangoModelFactory):
    class Meta:
        model = FilmWorkPerson

    job = factory.Faker('word', ext_word_list=PersonJob.values)


class FilmWorkGenreFactory(DjangoModelFactory):
    class Meta:
        model = FilmWorkGenre


class GenreFactory(DjangoModelFactory):
    class Meta:
        model = Genre

    genre = factory.Faker('word')
    description = factory.Faker('sentence', nb_words=32, variable_nb_words=True)
