from django.core.management.base import BaseCommand
from publet.projects.models import Publication


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for p in Publication.objects.all():
            self.stdout.write(p.slug + '\n')
            p.fix_article_order()
