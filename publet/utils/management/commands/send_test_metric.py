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
