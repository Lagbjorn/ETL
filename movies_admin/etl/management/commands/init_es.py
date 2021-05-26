import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from elasticsearch import Elasticsearch

from movies.models import DATETIME_ANCIENT, FilmWork

INDEX = 'movies'


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
        schema_dir = os.path.join(settings.STATIC_ROOT, 'etl/es_schema.json')
        with open(schema_dir) as f:
            request_body = json.load(f)
        if es.indices.exists(index=INDEX):
            es.indices.delete(index=INDEX)
        es.indices.create(index=INDEX, body=request_body)
        FilmWork.objects.all().update(indexed_at=DATETIME_ANCIENT)
