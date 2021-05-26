from django.core.management.base import BaseCommand

from etl.etl import ETL


class Command(BaseCommand):
    """
    Start ETL process
    """
    def handle(self, *args, **options):
        etl = ETL()
        etl.start()
