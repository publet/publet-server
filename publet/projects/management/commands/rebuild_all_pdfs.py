from django.core.management.base import BaseCommand, CommandError

from publet.projects.models import Publication
from publet.projects.tasks import rebuild_all_pdfs


class Command(BaseCommand):

    def log(self, msg):
        self.stdout.write(str(msg) + '\n')

    def handle(self, *args, **kwargs):
        publications = Publication.objects.all()
        result = rebuild_all_pdfs(publications)

        if not result:
            raise CommandError('Failed to rebuild pdfs')
