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
import logging
import time as _time
from contextlib import contextmanager
from functools import wraps

logger = logging.getLogger(__name__)

from django.conf import settings

try:
    from bernhard import Client, UDPTransport
except ImportError:
    # Just use a dummy client if we don't have a Riemann client installed.
    class Client(object):
        def __init__(self, *args, **kwargs):
            logger.warn('Using dummy client for metrics')

        def send(self, *args, **kwargs):
            pass

    UDPTransport = None


HOST = socket.gethostname()
ENABLED = getattr(settings, 'ENABLE_METRICS', False)
RIEMANN_HOST = getattr(settings, 'RIEMANN_HOST', '127.0.0.1')

c = Client(RIEMANN_HOST, transport=UDPTransport)


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

    if ENABLED:
        try:
            c.send(data)
        except:
            pass


class Metric(object):
    def __init__(self, name):
        self.name = name


class Occurrence(Metric):
    def mark(self):
        send(self.name, 'occurrence')


class Meter(Metric):
    def inc(self, n=1):
        send(self.name, 'meter', n)


class Histogram(Metric):
    def record(self, value):
        send(self.name, 'histogram', value)


class Gauge(Metric):
    def __init__(self, name):
        return super(Gauge, self).__init__('gauges.' + name)

    def report(self, value):
        send(self.name, 'gauge', value)


@contextmanager
def Timer(name):
    start = _time.time()

    # We fire a Meter for the metric here, because otherwise the
    # "events/sec" are recorded when they *end* instead of when they
    # begin.  For longer events this is a bad thing.
    Meter(name).inc()

    try:
        yield
    finally:
        ms = (_time.time() - start) * 1000
        send(name, 'timer', ms)


def time(f):
    """
    Report the running time of the decorated function to Riemann.

    The metric name will be generated automatically from the function
    module/name.  This may cause issues if the function is run from two
    separate import paths.  Python is dumb sometimes.
    """
    # Ugly hack to help normalize our crazy module names.
    path = f.__module__
    if path.startswith('apps.'):
        path = path[5:]

    name = 'functions.' + f.__module__ + '.' + f.__name__

    @wraps(f)
    def timed_f(*args, **kwargs):
        with Timer(name):
            return f(*args, **kwargs)

    return timed_f


def time_as(name):
    """
    Report the running time of the decorated function to Riemann with
    the given name.
    """
    def time_wrapper(f):
        @wraps(f)
        def timed_f(*args, **kwargs):
            with Timer(name):
                return f(*args, **kwargs)
        return timed_f
    return time_wrapper


class ManualTimer(Metric):
    def record(self, value):
        send(self.name, 'timer', value)
