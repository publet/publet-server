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
from datetime import datetime
from uuid import uuid4
from django.core.management.base import BaseCommand, CommandError
from publet.analytics.models import Event
from publet.analytics.core import get_social_source_by_referrer


class Command(BaseCommand):
    args = 'publication_id referrer num'

    def handle(self, *args, **kwargs):
        if len(args) != 3:
            raise CommandError('Wrong number of arguments')

        publication_id, referrer, num = args

        publication_id = int(publication_id)
        num = int(num)

        now = datetime.utcnow()
        social = get_social_source_by_referrer(referrer)

        for _ in range(0, num):
            anonymous_id = 'fudge-{}'.format(str(uuid4()))
            Event.objects.create(type='page', ip=1, anonymous_id=anonymous_id,
                                 publication_id=publication_id, created=now,
                                 referrer=referrer, social_referrer=social)
