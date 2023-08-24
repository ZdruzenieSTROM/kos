# pylint: disable=unused-wildcard-import,wildcard-import

from .test_settings import *

def secret(secret_name: str) -> str:
    secret_path = BASE_DIR / '.secrets' / secret_name

    return secret_path.read_text()

DEBUG = False

ADMINS = [('Kovacs', 'kovacs@strom.sk'), ('Masrna', 'michal.masrna@strom.sk')]

# Email Settings

SERVER_EMAIL = 'noreply@strom.sk'
DEFAULT_FROM_EMAIL = 'noreply@strom.sk'

# Email Backend Setup

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = '587'
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'noreply@strom.sk'
EMAIL_HOST_PASSWORD = secret('email_password.txt')
