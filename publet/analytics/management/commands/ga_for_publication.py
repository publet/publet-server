from django.core.management.base import BaseCommand, CommandError
from publet.projects.models import Publication
from publet.analytics.analytics import get_all_metrics_for_publication


class Command(BaseCommand):

    args = 'publication_pk'

    def handle(self, *args, **kwargs):
        if len(args) != 1:
            raise CommandError('Needs exactly one publication pk')

        publication = Publication.objects.get(pk=args[0])
        print get_all_metrics_for_publication(publication)
