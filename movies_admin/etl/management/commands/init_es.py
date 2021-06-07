import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from elasticsearch import Elasticsearch

from movies.models import DATETIME_ANCIENT, FilmWork, Genre, Person


class Command(BaseCommand):
    """
    Initialize ElasticSearch index for movies_admin app.
    Caution: existing index will be removed and created from scratch!
    `indexed_at` for all FilmWorks will be reset to default.
    """
    def handle(self, *args, **options):
        config = {
            'host': settings.ES_HOST,
            'port': settings.ES_PORT,
        }
        es = Elasticsearch([config, ])
        self._init_index(es, 'movies', 'etl/es_schema.json')
        self._init_index(es, 'persons', 'etl/es_schema_persons.json')
        self._init_index(es, 'genres', 'etl/es_schema_genres.json')

        FilmWork.objects.all().update(indexed_at=DATETIME_ANCIENT)
        Person.objects.all().update(indexed_at=DATETIME_ANCIENT)
        Genre.objects.all().update(indexed_at=DATETIME_ANCIENT)

    @staticmethod
    def _init_index(es, index_name, schema_path):
        schema_dir = os.path.join(settings.STATIC_ROOT, schema_path)
        with open(schema_dir) as f:
            request_body = json.load(f)
        if es.indices.exists(index=index_name):
            es.indices.delete(index=index_name)
        es.indices.create(index=index_name, body=request_body)
