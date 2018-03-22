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
from string import letters
from datetime import datetime, timedelta
from random import randint, choice
from django.core.management.base import BaseCommand
from publet.projects.models import Publication, PublicationSocialGateEntry
from publet.analytics.models import Event


def get_random_delta():
    return timedelta(hours=randint(0, 21), minutes=randint(0, 59),
                     days=randint(0, 100))


def randstr():
    return ''.join(map(lambda x: choice(letters), range(0, 10)))


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        """
        Generate fake gate entries and analytics events for the last 90
        days
        """
        slug = args[0]
        publication = Publication.objects.get(slug=slug)

        now = datetime.utcnow()
        social = ['twitter', 'twitter', 'twitter', 'facebook', 'facebook',
                  'linkedin', 'googleplus']
        blocks = publication.get_blocks()

        if not blocks:
            return

        if len(blocks) > 4:
            blocks = blocks[:4]

        for _ in range(0, 1000):
            ts = now - get_random_delta()
            s = choice(social)
            b = choice(blocks)

            PublicationSocialGateEntry.objects.create(
                publication=publication,
                block_id=b.id,
                created=ts,
                referrer=s,
                name=randstr(),
                email='%s@gmail.com' % randstr()
            )

            Event.objects.create(
                publication_id=publication.id,
                created=ts,
                social_referrer=s,
                ip=123,
                url='abc',
                type='engaged',
                seconds=randint(1, 1200)
            )

            Event.objects.create(
                publication_id=publication.id,
                created=ts,
                social_referrer=s,
                ip=123,
                url='abc',
                type='page'
            )
