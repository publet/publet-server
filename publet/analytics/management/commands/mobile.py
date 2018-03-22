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
from django.core.management.base import BaseCommand
from publet.analytics.models import Event
from publet.utils.utils import user_agent_to_device


class Command(BaseCommand):

    def handle(self, *args, **options):
        while True:
            events = Event.objects.filter(user_agent__isnull=False,
                                          device__isnull=True)

            print '{} left to do'.format(events.count())

            events = events[:1000]

            if not events:
                break

            print 'processing 1000 events...'

            for event in events:
                event.device = user_agent_to_device(event.user_agent)
                event.save()
