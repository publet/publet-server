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
