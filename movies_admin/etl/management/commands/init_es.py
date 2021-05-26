import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from elasticsearch import Elasticsearch


class Command(BaseCommand):
    """
    Init ES index
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
        es.indices.create(index='movies', body=request_body)
