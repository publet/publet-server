from django.core.management.base import BaseCommand
from publet.projects.models import Publication


class Command(BaseCommand):

    def handle(self, *args, **options):
        publications = Publication.objects.filter(new_style=True)
        n = publications.count()

        for i, p in enumerate(publications, start=1):
            print '[{}/{}] {}'.format(i, n, p.name)
            p.upload()
