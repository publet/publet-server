from django.core.management.base import BaseCommand, CommandError

from publet.projects.models import Publication
from publet.projects.tasks import rebuild_all_screenshots


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        publications = Publication.objects.all()
        result = rebuild_all_screenshots(publications)

        if not result:
            raise CommandError('Failed to rebuild screenshots')
