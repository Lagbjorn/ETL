import logging
from datetime import datetime
from functools import wraps
from typing import List

import backoff
from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import F, Q
from django.db.models.functions import Greatest
from elasticsearch import ConnectionError, Elasticsearch
from elasticsearch.helpers import bulk
from pydantic import ValidationError

from etl.models import BasePerson, FilmWorkES
from movies.models import FilmWork, Person, PersonJob

ETL_BATCH_SIZE = settings.ETL_BATCH_SIZE
ES_MAX_RECONNECTIONS = settings.ES_MAX_RECONNECTIONS

logger = logging.getLogger(__name__)


def coroutine(func):
    @wraps(func)
    def inner(*args, **kwargs):
        fn = func(*args, **kwargs)
        next(fn)
        return fn

    return inner


class ETL:
    """
    Container for ETL-specific methods
    The ETL process state is stored in models (field `FilmWork.indexed_at`)
    so there is no need in additional file- or Redis-based state storage
    """

    def __init__(self):
        pass

    def start(self):
        """Start ETL process using coroutines"""
        logger.info('Starting ETL process...')
        load_coroutine = self.load()
        transform_coroutine = self.transform(load_coroutine)
        self.extract(transform_coroutine)

        load_coroutine = self.load()
        transform_coroutine = self.transform_persons(load_coroutine)
        self.extract_persons(transform_coroutine)

    def extract(self, target):
        """Extract updated movies and related models"""
        while True:
            film_works = self.get_updated_movies()

            if not film_works:
                logger.debug('Got no FilmWorks to update')
                return
            else:
                count = len(film_works)
                logger.debug(f'Extracted {count} FilmWorks')
            target.send(film_works)

            # ensure we update indexed_at field
            indexed_at = datetime.now()
            for film in film_works:
                film.indexed_at = indexed_at
            # note that this will not apply to `modified` field
            # because of the default bulk_update implementation - and this is what we want
            FilmWork.objects.bulk_update(film_works, ['indexed_at'])

    @coroutine
    def transform(self, target):
        """Transform list of FilmWorks into the ElasticSearch format"""
        while True:
            film_works = (yield)
            count = len(film_works)
            docs = []
            for film in film_works:
                actors = [{'id': str(uuid), 'full_name': name}
                          for uuid, name in zip(film.actor_ids, film.actor_names)]
                writers = [{'id': str(uuid), 'full_name': name}
                           for uuid, name in zip(film.writer_ids, film.writer_names)]
                directors = [{'id': str(uuid), 'full_name': name}
                             for uuid, name in zip(film.director_ids, film.director_names)]
                try:
                    doc = FilmWorkES(id=str(film.id),
                                     title=film.title,
                                     rating=film.imdb_rating,
                                     genres=film.genres_list,
                                     writers_names=film.writer_names,
                                     actors_names=film.actor_names,
                                     directors_names=film.director_names,
                                     actors=actors,
                                     writers=writers,
                                     directors=directors,
                                     description=film.description)
                except ValidationError as e:
                    logger.error(f'Transform received invalid data associated with FilmWork with id {film.id}')
                    logger.error(e)
                    return
                doc = doc.dict()
                doc['_index'] = 'movies'
                doc['_id'] = str(film.id)
                docs.append(doc)
            target.send((docs, count))

    @coroutine
    def load(self):
        """Load data to ElasticSearch index"""
        config = {'host': settings.ES_HOST,
                  'port': settings.ES_PORT,
                  }
        es = Elasticsearch([config, ])
        logger.debug('Connected to ElasticSearch')
        while True:
            docs, count = (yield)
            self._bulk(es, docs)
            logger.debug(f'Indexed {count} docs')

    def extract_persons(self, target):
        while True:
            persons = self.get_updated_perons()

            if not persons:
                logger.debug('Got no Persons to update')
                return
            else:
                count = len(persons)
                logger.debug(f'Extracted {count} Persons')
            target.send(persons)

            # ensure we update indexed_at field
            indexed_at = datetime.now()
            for person in persons:
                person.indexed_at = indexed_at
            # note that this will not apply to `modified` field
            # because of the default bulk_update implementation - and this is what we want
            Person.objects.bulk_update(persons, ['indexed_at'])

    @coroutine
    def transform_persons(self, target):
        while True:
            persons = (yield)
            count = len(persons)
            docs = []
            for person in persons:
                try:
                    doc = BasePerson(id=str(person.id),
                                     full_name=person.name)
                except ValidationError as e:
                    logger.error(f'Transform received invalid data associated with Person with id {person.id}')
                    logger.error(e)
                    return
                doc = doc.dict()
                doc['_index'] = 'persons'
                doc['_id'] = str(person.id)
                docs.append(doc)
            target.send((docs, count))

    @staticmethod
    @backoff.on_exception(backoff.expo, ConnectionError, max_tries=ES_MAX_RECONNECTIONS)
    def _bulk(es, docs):
        """Bulk wrapped with backoff"""
        bulk(es, docs)

    def get_updated_movies(self) -> List[FilmWork]:  # not just FilmWork, but FilmWork with extra annotated fields
        """
        Get queryset with recently modified movies,
        movies with recently modified related entities or relations.
        """
        # annotate latest update of filmwork itself or related models
        last_db_update = Greatest('modified',
                                  'persons__modified',
                                  'genres__modified',
                                  'filmworkperson__modified',
                                  'filmworkgenre__modified')
        qs = FilmWork.objects.annotate(last_modified=last_db_update)

        # annotate related models using aggregation for easier transform
        qs = qs.annotate(genres_list=ArrayAgg('genres__genre',
                                              distinct=True))
        for job in PersonJob.values:
            jobs_ids = job + '_ids'  # like actors, writers and so on

            kwarg = {jobs_ids: ArrayAgg('persons__id',
                                        distinct=True,
                                        filter=Q(filmworkperson__job=job))}
            qs = qs.annotate(**kwarg)
            job_names = job + '_names'
            kwarg = {job_names: ArrayAgg('persons__name',
                                         distinct=True,
                                         filter=Q(filmworkperson__job=job))}
            qs = qs.annotate(**kwarg)

        # defer unneeded fields
        qs = qs.defer('persons',
                      'genres',
                      'creation_date',
                      'film_rating',
                      'film_type',
                      'created',
                      'modified')
        # filter by latest update, order by latest update (old comes first)
        qs = qs.filter(last_modified__gt=F('indexed_at'))
        qs = qs.order_by('last_modified')

        qs = qs[0:ETL_BATCH_SIZE]
        return list(qs)

    def get_updated_perons(self) -> List[Person]:  # not just FilmWork, but FilmWork with extra annotated fields
        """
        Get queryset with recently modified movies,
        movies with recently modified related entities or relations.
        """
        # annotate latest update of filmwork itself or related models
        last_db_update = Greatest('modified',
                                  'filmwork__modified',
                                  'filmworkperson__modified', )
        qs = Person.objects.annotate(last_modified=last_db_update)

        qs = qs.filter(last_modified__gt=F('indexed_at'))
        qs = qs.order_by('last_modified')

        qs = qs[0:ETL_BATCH_SIZE]
        return list(qs)
