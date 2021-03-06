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
import collections
import json
from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from publet.projects.models import Publication


EXCLUDE_SETS = ('bulkuserupload_set', 'publicationcoupon_set', 'purchase_set',)


def flatten(l):
    """
    Flatten a deeply nested list of lists
    """
    for el in l:
        if isinstance(el, collections.Iterable) \
                and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el


def get_sets(obj):
    """
    Get all properties that end with _set and aren't in the exclude list
    """
    sets = []

    for field in dir(obj):
        if field.endswith('_set') and field not in EXCLUDE_SETS:
            sets.append(field)

    return sets


def get_related(obj):
    """
    Return a flat list of all related objects.  The list is generated by
    descending the _set list to the bottom.
    """
    sets = get_sets(obj)

    if not sets:
        return obj

    result = [obj]

    for s in sets:
        objs = getattr(obj, s).all()

        if not objs:
            continue

        related = map(get_related, objs)

        if len(related) == 0:
            continue

        result.append(related)

    return flatten(result)


def assert_no_duplicates(data):
    """
    Make sure that we didn't include any duplicate objects
    """
    for c, i in data.items():

        pks = [m.pk for m in i]
        s = set(pks)

        assert len(pks) == len(s)


def organize_by_class(objs):
    per_class = {}

    for obj in objs:
        Class = obj.__class__.__name__

        if Class in per_class:
            e = per_class[Class]
            e.append(obj)
            per_class[Class] = e
        else:
            per_class[Class] = [obj]

    assert_no_duplicates(per_class)

    return per_class


class Command(BaseCommand):

    args = 'publication_pk'

    def log(self, msg):
        self.stdout.write(str(msg) + '\n')

    def handle(self, *args, **kwargs):
        if len(args) != 1:
            raise CommandError('Needs exactly one publication pk')

        publication_pk = int(args[0])

        try:
            pub = Publication.objects.get(pk=publication_pk)
        except Publication.DoesNotExist:
            raise CommandError('Publication does not exist')

        objs = list(get_related(pub))

        per_class = organize_by_class(objs)

        instances = []

        for Class, items in per_class.items():
            json_str = serializers.serialize('json', items)

            models = json.loads(json_str)

            for m in models:
                instances.append(m)

        assert len(instances) == len(objs)

        self.log(json.dumps(instances, indent=4))
