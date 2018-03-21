from django.core.management.base import BaseCommand
from publet.analytics.core import get_social_source_by_referrer
from publet.analytics.models import Event


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for ev in Event.objects.exclude(referrer=''):
            ev.social_referrer = get_social_source_by_referrer(ev.referrer)
            ev.save()
