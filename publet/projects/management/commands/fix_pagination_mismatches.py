from django.core.management.base import BaseCommand
from publet.projects.models import Publication


class Command(BaseCommand):

    def log(self, msg):
        self.stdout.write(str(msg) + '\n')

    def handle(self, *args, **kwargs):
        for p in Publication.objects.all():
            if p.pagination == p.type.pagination:
                continue

            self.log('Fixing {}'.format(p.slug))
            p.pagination = p.type.pagination
            p.save()
