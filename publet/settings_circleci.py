from settings import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'circle_test',
        'USER': 'ubuntu',
        # 'ENGINE': 'django.db.backends.sqlite3',
        # 'NAME': 'dev.db',
    }
}

EPUB_GENERATION_BIN = 'ebook-convert'
PDF_GENERATION_BIN = '/bin/wkhtmltopdf'

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
USE_HTTPS = False
SESSION_COOKIE_DOMAIN = '.example.com'

INSTALLATION = 'ci'
ENABLE_METRICS = False
RIEMANN_HOST = '127.0.0.1'
CELERY_ALWAYS_EAGER = True

TESTING = True

STRIPE_PUBLISHABLE_KEY = 'abc'
STRIPE_SECRET_KEY = 'abc'
SOUTH_TESTS_MIGRATE = False
HOST = 'http://testing.publet.com'

BUFFER_OAUTH_CALLBACK = ''
BUFFER_OAUTH_CLIENT_ID = ''

BUFFER_OAUTH_ACCESS_TOKEN = ''
BUFFER_OAUTH_CLIENT_SECRET = ''


class DisableMigrations(object):

    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return "notmigrations"


MIGRATION_MODULES = DisableMigrations()

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    },
    'session': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}


REACT_BUILD_URL = ''
