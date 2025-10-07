# core/management/commands/create_prod_superuser.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    """Creates a superuser for the production environment non-interactively."""

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'admin'  # Or your desired username
        email = 'admin@example.com'
        password = 'a-very-strong-temporary-password' # IMPORTANT: Change this!

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists."))
        else:
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f"Successfully created superuser '{username}'"))