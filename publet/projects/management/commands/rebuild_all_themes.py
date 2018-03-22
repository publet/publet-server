"""
Publet
Copyright (C) 2018  Publet Inc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
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
