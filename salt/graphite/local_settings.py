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
