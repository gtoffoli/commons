from __future__ import unicode_literals

from django.core import management
from django.utils.crypto import get_random_string


class Command(management.BaseCommand):
    help = 'Gets CommonS + Mayan EDMS ready to be used (initializes database, creates a secret key, etc).'

    def _generate_secret_key(self):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        return get_random_string(50, chars)

    def handle(self, *args, **options):
        management.call_command('syncdb', migrate=True, interactive=False)
