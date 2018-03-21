from itertools import groupby
from uuid import uuid4

from django.core.management.base import BaseCommand

from publet.analytics.models import Event


class Command(BaseCommand):

    def handle(self, *args, **options):
        events = Event.objects.filter(anonymous_id__isnull=True,
                                      ip__isnull=False)

        print events.count(), 'events to process'

        events = groupby(events, lambda x: x.ip)

        for ip, _ in events:
            anonymous_id = uuid4()
            Event.objects.filter(ip=ip).update(anonymous_id=anonymous_id)

        events = Event.objects.filter(anonymous_id__isnull=True,
                                      ip__isnull=True)

        print events.count(), 'events with anonymous_id and ip null'
        events.delete()
