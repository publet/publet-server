from django.core.management.base import BaseCommand, CommandError
from annoying.functions import get_object_or_None
from publet.projects.models import Theme, SassException
from publet.projects.tasks import rebuild_themes


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('theme_slug', type=str, nargs='?')

    def update_theme(self, theme):
        try:
            theme.save(update_on_disk=False)
            theme.update_theme_on_disk(collect_static=False)
            self.stdout.write('* {} updated\n'.format(theme.slug))
        except SassException:
            raise CommandError('failed theme {}\n'.format(theme.slug))

    def handle(self, *args, **options):
        slug = options.get('theme_slug', None)

        if slug:
            theme = get_object_or_None(Theme, slug=slug)

            if not theme:
                raise CommandError('Theme not found')

            self.update_theme(theme)

            return

        themes = Theme.objects.select_related().all()
        result = rebuild_themes(themes)

        if not result:
            raise CommandError('Failed to rebuild themes')
