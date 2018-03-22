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
from random import choice, randint
from datetime import datetime, timedelta
from uuid import uuid4
from annoying.functions import get_object_or_None
from django.core.management.base import BaseCommand, CommandError
from publet.analytics.models import Event
from publet.analytics.core import get_social_source_by_referrer
from publet.projects.models import GateSubmission, Publication


first_names = ['John', 'Peter', 'Sarah', 'Elizabeth', 'Margaret', 'Leah',
               'Kate', 'Li', 'Pedro', 'Lisa', 'Maria', 'Joseph', 'Abraham',
               'Jose', 'William', 'James', 'David', 'Robert', 'Steven',
               'Nicole', 'Rebecca', 'Natasha', 'Theresa']
last_names = ['Smith', 'Johnson', 'Robinson', 'Cheng', 'Gonzales', 'Escobar',
              'Martinez', 'Williams', 'Wilson', 'White', 'Walker', 'Walker',
              'Evans', 'Parker', 'Cooper', 'Kelly', 'Sanders', 'Russell']
action_names = ['Click header', 'Click header', 'Click navigation',
                'Click CTA']


def get_referrer():
    return choice(['t.co', 'facebook.com'])


class Command(BaseCommand):
    args = 'publication_id num_people'

    def handle(self, *args, **kwargs):
        if len(args) != 2:
            raise CommandError('Wrong number of arguments')

        publication_id, num = args

        publication_id = int(publication_id)
        num = int(num)

        publication = get_object_or_None(Publication, pk=publication_id)

        if not publication:
            raise CommandError('Publication not found')

        if not publication.new_style:
            raise CommandError('Only new style publications are supported')

        now = datetime.utcnow()
        referrer = get_referrer()
        social = get_social_source_by_referrer(referrer)

        articles = publication.articles().all()

        for _ in range(0, num):
            rand = randint(0, 100)
            anonymous_id = 'fudge-{}'.format(str(uuid4()))

            t = now - timedelta(days=randint(1, 29))

            for _ in range(0, 10):
                article_id = choice(articles).pk
                Event.objects.create(type='page', ip=1,
                                     anonymous_id=anonymous_id,
                                     publication_id=publication_id, created=t,
                                     referrer=referrer, social_referrer=social)

                Event.objects.create(type='engaged_publication', ip=1,
                                     seconds=randint(0, 200),
                                     anonymous_id=anonymous_id,
                                     publication_id=publication_id, created=t,
                                     referrer=referrer, social_referrer=social)

                Event.objects.create(type='engaged_article', ip=1,
                                     seconds=randint(0, 200),
                                     anonymous_id=anonymous_id,
                                     article_id=article_id,
                                     publication_id=publication_id, created=t,
                                     referrer=referrer, social_referrer=social)

                Event.objects.create(type='read_publication', ip=1,
                                     percent_read=randint(1, 99),
                                     anonymous_id=anonymous_id,
                                     publication_id=publication_id, created=t,
                                     referrer=referrer, social_referrer=social)

                Event.objects.create(type='read_article', ip=1,
                                     percent_read=randint(1, 99),
                                     article_id=article_id,
                                     anonymous_id=anonymous_id,
                                     publication_id=publication_id, created=t,
                                     referrer=referrer, social_referrer=social)

            if rand < 10:
                data = {
                    'first_name': choice(first_names),
                    'last_name': choice(last_names)
                }
                g = GateSubmission.objects.create(
                    publication_id=publication_id,
                    data=data,
                    anonymous_id=anonymous_id)
                g.created = t
                g.save()

            if rand < 20:
                Event.objects.create(type='action', ip=1, action_type='click',
                                     action_name=choice(action_names),
                                     action_value=1,
                                     publication_id=publication_id,
                                     anonymous_id=anonymous_id,
                                     created=t,
                                     referrer=referrer, social_referrer=social)
