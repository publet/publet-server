# Django settings for publet project.

import os
import logging

DEBUG = True
TEMPLATE_DEBUG = DEBUG

BASE_PATH = os.path.dirname(__file__)
PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
MANAGEPY_DIR = os.path.abspath(os.path.join(PROJECT_PATH, '../'))

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

INTERNAL_IPS = ('127.0.0.1',)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
# MEDIA_ROOT = os.path.join(BASE_PATH, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
# STATIC_ROOT = os.path.join(BASE_PATH, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(BASE_PATH, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

STATICFILES_STORAGE = 'publet.projects.storage.PubletCachedStaticFilesStorage'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '0@%9@ci+t62adj^8f+n+$k59lky8eti=%t@9@i-gmdf()5&amp;4t('

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'publet.projects.context_processors.add_current_commit',
    'publet.projects.context_processors.add_intercom',
    'publet.projects.context_processors.add_filepicker_policy',
    'publet.projects.context_processors.add_filepicker_api_key',
    'publet.projects.context_processors.add_host',
    'publet.projects.context_processors.add_google_analytics_id',
    'publet.projects.context_processors.add_livereload',
    'publet.projects.context_processors.add_all_users',
    'publet.projects.context_processors.add_ip_as_int',
    'publet.projects.context_processors.add_can_impersonate',
    'publet.projects.context_processors.add_features',
    'publet.projects.context_processors.add_track_host',
)

MIDDLEWARE_CLASSES = (
    'publet.projects.middleware.ResponseTimeMiddleware',  # Must be first
    'publet.projects.middleware.MultiHostMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'publet.projects.middleware.CommonMiddleware',
    'publet.projects.middleware.UserAgentMiddleware',
    'publet.projects.middleware.FeatureMiddleware',
    'publet.projects.middleware.PublicationDomainMiddleware',
    'publet.projects.middleware.ImpersonateMiddleware',
    'django_cprofile_middleware.middleware.ProfilerMiddleware'
)

ROOT_URLCONF = 'publet.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'publet.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, 'templates'),
)

INSTALLED_APPS = (

    # Django built-ins
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'flat',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'django.contrib.humanize',

    # Third-party
    'postmark',
    'registration',
    'tastypie',
    'django_rq',

    # TODO: Debug toolbar causes tastypie's `backfill_api_keys` to fail
    # 'debug_toolbar',

    # Publet apps
    'publet.users',
    'publet.common',
    'publet.fonts',
    'publet.groups',
    'publet.payments',
    'publet.projects',
    'publet.reader',
    'publet.outputs',
    'publet.utils',
    'publet.metrics',
    'publet.docs',
    'publet.analytics',
    'publet.third',
    'publet.debug',
    'publet.feedback',

)

# Flatpages
SITE_ID = 1

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django': {}
    },
}

# Get all the existing loggers
root = logging.root
existing = root.manager.loggerDict.keys()

# Set them explicitly to a blank value so that they are overidden
# and propogate to the root logger
for logger in existing:
    LOGGING['loggers'][logger] = {}

# Authentication
# AUTH_PROFILE_MODULE = 'utils.UserProfile'
ACCOUNT_ACTIVATION_DAYS = 7
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'

ARTICLE_DOMAIN_IGNORED_HOSTS = (
    'publet.com', 'beta.publet.com', 'www.publet.com', 'publet.example.com',
    'publet.example.com:8080', 'localhost', 'localhost:4000', 'localhost:8000',
    '127.0.0.1:8000', 'staging.publet.com', 'pblt.co', 'pblt.example.com',
    'staging.pblt.co', 'beta-2.publet.com', 'staging-2.publet.com',
    'publet.example.com:8000', 'editor-staging.publet.com',
    'editor-staging-2.publet.com', 'track.publet.com', 'editor-2.publet.com',
    'editor.publet.com', 'theme-staging-2.publet.com',
    'theme-staging.publet.com', 'article-staging-2.publet.com',
    'article-staging.publet.com', 'article.publet.com', 'theme.publet.com',
    'article-beta-2.publet.com', 'theme-beta-2.publet.com',
    'sandbox.publet.com', 'sandbox-beta-2.publet.com',
    'sandbox-staging.publet.com', 'sandbox-staging-2.publet.com',
    'insights-staging.publet.com', 'insights-staging-2.publet.com',
    'insights.publet.com', 'insights-beta-2.publet.com',
    'settings.publet.com', 'settings-staging.publet.com',
    'settings-beta-2.publet.com', 'settings-staging-2.publet.com',
)

try:
    CURRENT_COMMIT = open(os.path.join(PROJECT_PATH, '../.current-commit')).read()
except:
    CURRENT_COMMIT = None

ENABLE_METRICS = True
RIEMANN_HOST = 'metrics.publet.com'

INSTALLATION = 'production'

RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        'PASSWORD': None,
        'DEFAULT_TIMEOUT': 0,
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'VERSION': 0,
        "LOCATION": "redis://127.0.0.1:6379/0",
        'OPTIONS': {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PARSER_CLASS": "redis.connection.HiredisParser",
        },
    },
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'VERSION': 0,
        "LOCATION": "redis://127.0.0.1:6379/0",
        'OPTIONS': {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PARSER_CLASS": "redis.connection.HiredisParser",
            "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
        },
    },
}

MOBILE_APP_DIR = '/opt/publet/mobile/apps'

USE_LIVE_RELOAD = True

GOOGLE_ANALYTICS_API_CREDS = {
    "_class": "OAuth2Credentials",
    "_module": "oauth2client.client",
    "access_token": "ya29.1.AADtN_VRGx27xCGjgGmQrXmGnxiQMeGyJiy9z8elSpjzikgwuyFmJLKuFH5Zc6o",
    "client_id": "126319164316-5ppab3uepuos71cqmc1sagf7u1lds5rt.apps.googleusercontent.com",
    "client_secret": "Z9UrxSwaRkuXChCGMmxz7fYa",
    "id_token": None,
    "invalid": False,
    "refresh_token": "1/aXRAFw2Bw7m8Vj17ustbJrxhN6r6Dp_tJGO1HDlG4vk",
    "revoke_uri": "https://accounts.google.com/o/oauth2/revoke",
    "token_expiry": "2014-02-20T11:08:48Z",
    "token_response": {
        "access_token": "ya29.1.AADtN_VRGx27xCGjgGmQrXmGnxiQMeGyJiy9z8elSpjzikgwuyFmJLKuFH5Zc6o",
        "expires_in": 3600,
        "refresh_token": "1/aXRAFw2Bw7m8Vj17ustbJrxhN6r6Dp_tJGO1HDlG4vk",
        "token_type": "Bearer"
    },
    "token_uri": "https://accounts.google.com/o/oauth2/token",
    "user_agent": None
}

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'publet.projects.middleware.should_show_debug_toolbar'
}

BROKER_USERNAME = 'brokerbot'
SHORT_HOST = 'pblt.example.com'

SLACK_WEBHOOK_FEEDBACK = 'https://hooks.slack.com/services/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'
SLACK_WEBHOOK_SALES = 'https://hooks.slack.com/services/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'

BUFFER_OAUTH_CALLBACK = ''
BUFFER_OAUTH_CLIENT_ID = ''
BUFFER_OAUTH_ACCESS_TOKEN = ''
BUFFER_OAUTH_CLIENT_SECRET = ''

USER_MODEL = 'users.PubletUser'
AUTH_USER_MODEL = USER_MODEL

AUTHENTICATION_BACKENDS = (
    'publet.users.backend.PubletAuthBackend',
)

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
SESSION_COOKIE_NAME = 'publetid'
SESSION_CACHE_ALIAS = 'session'

GENERATED_PUBLICATIONS_PATH = '/opt/publet/static/css/outputs/generated/'

# After 30mins of inactivity, if the user comes back, we treat their visit as a
# new session
TRACKING_SESSION_LENGTH = 30 * 60  # 30mins

ELASTICSEARCH_CONFIG = ['localhost:9200']

REACT_BUILD_URL = ''
TRACK_URL = 'ws://track.example.com:3000'

AWS_ACCESS_KEY_ID = 'AKIAIU5WCE4LRFUSLMSA'
AWS_SECRET_ACCESS_KEY = '57TcxDEi/hiC5WfDABrL3MK6mlDj/DOFDdr2YioS'
AWS_BUCKET_PUBLICATIONS = 'publications-staging'

ARTICLE_EDITOR_BASE_URL = 'https://editor'
THEME_EDITOR_BASE_URL = 'https://theme-staging.publet.com'
PREVIEW_URL = 'http://publications-staging.publet.com'
SETTINGS_URL = 'https://settings-staging.publet.com'
VARNISH_PURGE_SECRET = 'g)@xfmvz2vgdwc3lxq62m99fjs2mp^74sbc5+_79-qd(5w$0!c'
VARNISH_PURGE_PORT = 3000

REGISTRATION_EMAIL_HTML = False

try:
    from settings_local import *
except ImportError:
    pass
