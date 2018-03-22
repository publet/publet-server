"""
Publet
Copyright (C) 2018  Publet Inc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from settings import *

GEO_DB_NAME = 'geo'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'publet',
        'USER': 'postgres',
    },
    GEO_DB_NAME: {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': GEO_DB_NAME,
        'USER': 'postgres',
    }
}

EPUB_GENERATION_BIN = 'ebook-convert'
PDF_GENERATION_BIN = '/usr/local/bin/wkhtmltopdf'
IMAGE_GENERATION_BIN = '/usr/local/bin/wkhtmltoimage'

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
USE_HTTPS = False
SESSION_COOKIE_DOMAIN = '.example.com'

INSTALLATION = 'dev'
DOMAIN = 'publet.example.com:8080'
HOST = 'http://publet.example.com:8080'
ENABLE_METRICS = False
RIEMANN_HOST = '127.0.0.1'

TASTYPIE_FULL_DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CACHES = {
    'default': {
        # 'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/0',
        # 'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
    },
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        }
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "session"

CELERY_ALWAYS_EAGER = False
STATIC_ROOT = '/opt/publet/static'
REACT_BUILD_URL = 'https://build-staging.publet.com'
AWS_BUCKET_PUBLICATIONS = 'publications-staging'

ARTICLE_EDITOR_BASE_URL = 'https://editor-staging.publet.com'
ARTICLE_EDITOR_BASE_URL = 'http://editor-publet.example.com:1337'
TRACK_URL = 'ws://track.example.com:3300'
