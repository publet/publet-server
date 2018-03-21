from django.core.management.base import BaseCommand, CommandError
from annoying.functions import get_object_or_None

from publet.projects.models import Theme


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        theme = get_object_or_None(Theme, slug=args[0])

        if not theme:
            raise CommandError('Theme not found')

        print theme.render_theme_scss()
