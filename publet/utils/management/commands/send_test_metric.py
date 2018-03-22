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
import socket
from django.conf import settings
from django.core.management.base import BaseCommand
from bernhard import Client, TCPTransport


HOST = socket.gethostname()
ENABLED = getattr(settings, 'ENABLE_METRICS', False)
RIEMANN_HOST = getattr(settings, 'RIEMANN_HOST', '127.0.0.1')

c = Client(RIEMANN_HOST, transport=TCPTransport)


def find_environment_tag():
    return getattr(settings, 'INSTALLATION', None)


ENV_TAG = find_environment_tag()


def send(service, tag, metric=None):
    data = {
        'host': HOST,
        'service': service,
        'tags': [tag, ENV_TAG]
    }

    if metric:
        data['metric'] = metric

    c.send(data)


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        send('publet-test', 'occurrence')
