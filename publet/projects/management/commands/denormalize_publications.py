from django.core.management.base import BaseCommand, CommandError
from annoying.functions import get_object_or_None
from publet.projects.models import Publication


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('publication_slug', type=str, nargs='?')

    def handle(self, *args, **options):
        slug = options.get('publication_slug', None)

        if slug:
            p = get_object_or_None(Publication, slug=slug)

            if not p:
                raise CommandError('Publication not found')

            p.cache_json()
            p.save()

            return

        for p in Publication.objects.all():
            self.stdout.write(p.slug + '\n')
            p.cache_json()
            p.save()
