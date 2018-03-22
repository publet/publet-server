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
