from settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'publet',
        'USER': 'postgres',
    }
}

EPUB_GENERATION_BIN = '/Applications/calibre.app/Contents/MacOS/ebook-convert'
PDF_GENERATION_BIN = '/usr/local/bin/wkhtmltopdf'
IMAGE_GENERATION_BIN = '/usr/local/bin/wkhtmltoimage'

DOMAIN = 'publet.example.com:8000'
HOST = 'http://publet.example.com:8000'

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
USE_HTTPS = False
SESSION_COOKIE_DOMAIN = '.example.com'

CELERY_ALWAYS_EAGER = True

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache'
    },
    'session': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache'
    }
}

STATIC_ROOT = 'static-root'
