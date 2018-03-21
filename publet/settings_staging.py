import os
from settings import *

BASE_PATH = os.path.dirname(__file__)

DEBUG = False

ADMINS = ()

GEO_DB_NAME = 'geo'

db_user = os.getenv('DB_USER', 'publet')
db_password = os.getenv('DB_PASSWORD', 'ahP5A7CkOcN7Mgo8lbRtPto4F6xnsihHJh')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'publet',
        'USER': db_user,
        'PASSWORD': db_password,
        'HOST': 'localhost',
        'PORT': '',
    },
    GEO_DB_NAME: {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': GEO_DB_NAME,
        'USER': db_user,
        'PASSWORD': db_password,
        'HOST': 'localhost',
        'PORT': '',
    }
}

INSTALLED_APPS = INSTALLED_APPS + ('raven.contrib.django.raven_compat',)

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = "/opt/publet/media"

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = 'https://staging.publet.com/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = "/opt/publet/static"

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = 'https://staging.publet.com/static/'

# Email
DEFAULT_FROM_EMAIL = 'support@publet.com'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_BACKEND = 'postmark.django_backend.EmailBackend'
POSTMARK_API_KEY = 'fd6d6d5c-c214-4271-a6ec-153d5dec155e'

# Django 1.5+ requires specific hostnames to be defined.
ALLOWED_HOSTS = ['*']
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_DOMAIN = '.publet.com'
SESSION_COOKIE_SECURE = False
USE_HTTPS = True

# Sentry.
RAVEN_CONFIG = {
    'dsn': 'https://ed0de1c1f0db44fe88ae34ab9beb1731:5d8eef6eabcd41dea69c9deaac9e13ef@app.getsentry.com/36987'
}

EPUB_GENERATION_BIN = 'ebook-convert'
PDF_GENERATION_BIN = '/usr/local/bin/wkhtmltopdf'
IMAGE_GENERATION_BIN = '/usr/local/bin/wkhtmltoimage'

# Stripe
STRIPE_PUBLISHABLE_KEY = 'pk_test_eEAl268PpHzMtNR1zx2Hhubn'
STRIPE_SECRET_KEY = 'sk_test_r65oTWUtgu4q3UAqJ0gOGLVf'

# Filepicker
FILEPICKER_API_KEY = 'AH5FfH2wSbOnW3MKuxIjgz'
FILEPICKER_SECRET = 'FZUSTUIZ2VGG7CKP32UVGY6VLI'

INSTALLATION = 'staging'
DOMAIN = 'staging.publet.com'
HOST = 'https://staging.publet.com'
ENABLE_METRICS = True
RIEMANN_HOST = 'metrics.publet.com'

INTERCOM_APP_ID = '6d2e5754e612db9841154b0113bb060a643b664b'

GOOGLE_ANALYTICS_ID = 'UA-47665550-2'

TESTING = False

LOGGING['handlers']['sentry'] = {
    'level': 'ERROR',
    'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
}
LOGGING['root']['handlers'].append('sentry')

SHORT_HOST = 'staging.pblt.co'

BUFFER_OAUTH_CALLBACK = 'https://staging.publet.com/third/buffer/oauth/callback'
BUFFER_OAUTH_CLIENT_ID = '549159564c9660ab369c7827'
BUFFER_OAUTH_ACCESS_TOKEN = '1/965e2a15aa7b54c6b3727bf5600400a2'
BUFFER_OAUTH_CLIENT_SECRET = '268ccd3e6c51fe24e87de66be0013ac1'

TRACK_URL = 'wss://track-staging.publet.com'

REACT_BUILD_URL = 'https://build-staging.publet.com'
AWS_BUCKET_PUBLICATIONS = 'publications-staging'

ARTICLE_EDITOR_BASE_URL = 'https://article-staging.publet.com'
SETTINGS_URL = 'https://settings-staging.publet.com'
