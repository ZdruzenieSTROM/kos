# pylint: disable=unused-wildcard-import,wildcard-import

from .test_settings import *


def secret(secret_name: str) -> str:
    secret_path = BASE_DIR / '.secrets' / secret_name

    return secret_path.read_text()


DEBUG = False

SECRET_KEY = secret('django_secret_key.txt')

ADMINS = [('Kovacs', 'kovacs@strom.sk'), ('Masrna', 'michal.masrna@strom.sk')]

# Email Settings

DEFAULT_FROM_EMAIL = 'noreply@strom.sk'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Email Backend Setup

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp-relay.gmail.com'
EMAIL_PORT = '587'
EMAIL_USE_TLS = True
