DATABASE_ENGINE = 'django.db.backends.postgresql_psycopg2'
DATABASE_NAME = 'graphite'
DATABASE_USER = 'graphite'
DATABASE_PASSWORD = 'postgres'
DATABASE_HOST = ''
DATABASE_PORT = ''

CONF_DIR = "{{ pillar.confdir }}"
LOG_DIR = "{{ pillar.logdir }}"

SECRET_KEY = "{{ pillar.secret_key }}"
TIME_ZONE = 'UTC'
