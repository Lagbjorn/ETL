import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    """
    Create superuser from env variables
    """
    def handle(self, *args, **options):
        user_model = get_user_model()

        user = os.getenv('SUPERUSER')
        password = os.getenv('SUPERUSER_PASSWORD')
        if not user_model.objects.filter(username=user).exists():
            user_model.objects.create_superuser(username=user, password=password)
