import sys
from settings_vagrant import *


class DisableMigrations(object):

    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return "notmigrations"


MIGRATION_MODULES = DisableMigrations()

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    },
    'session': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': 'dev.db',
#     }
# }

CELERY_ALWAYS_EAGER = True
ENABLE_METRICS = False
TESTING = True

SOUTH_TESTS_MIGRATE = False
STATIC_ROOT = '/tmp'
HOST = 'http://testing.publet.com'

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)
