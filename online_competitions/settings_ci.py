"""Isolated settings for CI; never connect checks to a deployment database."""
from pathlib import Path
from tempfile import gettempdir

from .settings.test_settings import *  # noqa: F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
STATIC_ROOT = Path(gettempdir()) / 'strom-kos-static'
ALLOWED_HOSTS = ['localhost', 'testserver']
