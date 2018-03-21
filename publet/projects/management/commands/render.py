from django.core.management.base import BaseCommand, CommandError
from annoying.functions import get_object_or_None

from publet.projects.models import Publication


class Command(BaseCommand):

    args = '<pub slug> <ext>'

    def handle(self, *args, **kwargs):

        if len(args) != 2:
            raise CommandError('wrong args')

        publication_slug, ext = args

        if ext not in ('html', 'pdf', 'epub', 'mobi', 'jpg',):
            raise CommandError('wrong ext')

        publication = get_object_or_None(Publication, slug=publication_slug)

        if not publication:
            raise CommandError('publication not found')

        publication._render_css()
        publication._render_js()
        publication.render_ext(ext, sync=True)
