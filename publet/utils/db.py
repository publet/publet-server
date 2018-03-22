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
from contextlib import contextmanager

from django.conf import settings
from django.db import connection


@contextmanager
def no_queries_allowed():
    """
    This is a helper method that makes it easier during development, by
    throwing an exception when any queries are made within its block.
    Using an ORM, it's sometimes hard to discover what statements lead
    to implicit queries.  Wrapping this contextmanager around such
    blocks makes sure that this cannot happen.

    This is only works in debug mode, as in non-debug mode the
    connection.queries list isn't available for inspection.  In
    production, this is a no-op.
    """
    if settings.DEBUG or settings.TESTING:
        queries = connection.queries
        num_queries = len(queries)
    yield
    if settings.DEBUG or settings.TESTING:
        assert num_queries == len(queries), \
            "A query was made, but this was explicitly forbidden! " \
            "Queries were: {}".format(queries[num_queries:])


@contextmanager
def query_count():
    if settings.DEBUG or settings.TESTING:
        num_queries = len(connection.queries)
        yield
        print 'Queries:', len(connection.queries) - num_queries
    else:
        yield
