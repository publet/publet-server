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
from random import randint, choice
from datetime import datetime, timedelta
from uuid import uuid4
from django.core.management.base import BaseCommand, CommandError
from publet.analytics.models import Event, get_date_range
from publet.analytics.core import get_social_source_by_referrer
from publet.projects.models import Publication, TextBlock


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('publication_slug', type=str)

    def handle(self, *args, **options):
        publication_slug = options.get('publication_slug')

        try:
            publication = Publication.objects.get(slug=publication_slug)
        except Publication.DoesNotExist:
            raise CommandError('Publication not found')

        events = []

        end = datetime.utcnow()
        start = end - timedelta(days=30)

        number_of_users = randint(1000, 5000)

        date_range = get_date_range(start, end)

        referrers = [
            'https://t.co',
            'https://www.facebook.com',
            'https://www.linkedin.com',
            'https://lnkd.in',
            'https://plus.google.com'
        ]

        print 'Adding events for', number_of_users, 'of users'

        text_block_ids = [
            tb.pk for tb in
            TextBlock.objects.filter(article__publication=publication)
        ]

        text_block_ids.append(None)

        for _ in range(0, number_of_users):
            anonymous_id = 'fudge-{}'.format(str(uuid4()))
            ip = 1

            number_of_visits = randint(10, 100)

            for _ in range(0, number_of_visits):
                ts = choice(date_range)
                r = choice(referrers)
                s = get_social_source_by_referrer(r)
                b = choice(text_block_ids)

                e = Event(type='page', ip=ip, anonymous_id=anonymous_id,
                          publication_id=publication.id, created=ts,
                          referrer=r, social_referrer=s, block_id=b)

                events.append(e)

        print 'Collected', len(events), 'events'
        Event.objects.bulk_create(events)
