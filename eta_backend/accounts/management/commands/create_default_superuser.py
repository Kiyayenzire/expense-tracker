import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a default superuser if the environment variables are configured and no user exists.'

    def handle(self, *args, **options):
        username = (os.getenv('DJANGO_SUPERUSER_USERNAME') or '').strip()
        email = (os.getenv('DJANGO_SUPERUSER_EMAIL') or '').strip()
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD') or ''

        if not username or not email or not password:
            self.stdout.write(self.style.WARNING('Default superuser not configured: set DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, and DJANGO_SUPERUSER_PASSWORD.'))
            return

        existing_user = User.objects.filter(username__iexact=username).first() or User.objects.filter(email__iexact=email).first()
        if existing_user:
            self.stdout.write(self.style.SUCCESS(f'Default superuser already exists: {existing_user.username}'))
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(f'Created default superuser: {user.username} ({user.email})'))
