from django.core.management.base import BaseCommand
from publet.projects.models import Publication
from publet.projects.tasks import upload_new_publication


class Command(BaseCommand):

    def handle(self, *args, **options):
        publications = Publication.objects.filter(
            new_style=True).order_by('-modified')

        for p in publications:
            upload_new_publication.delay(p.pk)

        print '{} publications scheduled for rebuilding'.format(
            publications.count())
