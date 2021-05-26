import json
import logging
from datetime import datetime
from functools import wraps
from pprint import pprint
from typing import List

from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import F, Q
from django.db.models.functions import Greatest
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from movies.models import FilmWork, PersonJob

BATCH_SIZE = 100
DATETIME_ANCIENT = datetime(year=2020, month=1, day=1, hour=0, minute=0)
TIME_FORMAT = '%d.%m.%y %H:%M:%S.%f'


def coroutine(func):
    @wraps(func)
    def inner(*args, **kwargs):
        fn = func(*args, **kwargs)
        next(fn)
        return fn

    return inner

logger = logging.getLogger(__name__)


class ETL:
    """
    Container for ETL-specific methods
    The ETL process state is stored in models (field `FilmWork.indexed_at`)
    so there is no need in additional file- or Redis-based state storage
    """
    def __init__(self):
        pass

    def start(self):
        """Start ETL process"""
        logger.info('Starting ETL process...')
        load_coroutine = self.load()
        transform_coroutine = self.transform(load_coroutine)
        self.extract(transform_coroutine)

    def extract(self, target):
        """Extract updated movies and related models"""
        while True:
            logger.info('Starting extract process...')
            film_works = self.get_updated_movies()
            if not film_works:
                logger.info('Got no FilmWorks to update')
                return
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
            logger.info(f'Starting transform process for {count} FilmWorks...')
            docs = []
            for film in film_works:
                doc = {
                    '_index': 'movies',
                    '_id': str(film.id),
                    'id': str(film.id),
                    'title': film.title,
                    'imdb_rating': film.imdb_rating,
                    'genre': ', '.join(film.genres_list),
                    'writers_names': ', '.join(film.writers),
                    'actors_names': ', '.join(film.actors),
                    'director': ', '.join(film.directors),
                    'description': film.description,
                }
                docs.append(doc)
            target.send(docs)

    @coroutine
    def load(self):
        """Load data to ElasticSearch index"""
        logger.info('Attempting connection to ElasticSearch')
        config = {'host': settings.ES_HOST,
                  'port': settings.ES_PORT,
                  }
        es = Elasticsearch([config, ])
        logger.info('Connected to ElasticSearch')
        while True:
            docs = (yield)
            logger.info('Starting transform process...')
            bulk(es, docs)

    def get_updated_movies(self) -> List[FilmWork]:  # not just FilmWork, but FilmWork with extra annotated fields
        """
        Get queryset with recently modified movies,
        movies with recently modified related entities or relations.
        """
        last_db_update = Greatest('modified',
                                  'persons__modified',
                                  'genres__modified',
                                  'filmworkperson__modified',
                                  'filmworkgenre__modified')
        # annotate latest update of filmwork itself or related models
        qs = FilmWork.objects.annotate(last_modified=last_db_update)

        # annotate related models using aggregation for easier transform
        qs = qs.annotate(genres_list=ArrayAgg('genres__genre', distinct=True))
        for job in PersonJob.values:
            jobs_list = job + 's'  # like actors_list, writers_list and so on
            kwarg = {jobs_list: ArrayAgg('persons__name', distinct=True, filter=Q(filmworkperson__job=job))}
            qs = qs.annotate(**kwarg)

        # filter by latest update, order by latest update (old comes first)
        qs = qs.filter(last_modified__gt=F('indexed_at')).order_by('last_modified')
        qs = qs[0:BATCH_SIZE]
        return list(qs)
