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
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from publet.groups.models import Group
from publet.projects.models import Theme


class Command(BaseCommand):

    args = 'src_group_slug dest_group_slug'
    option_list = BaseCommand.option_list + (
        make_option('--all',
                    action='store_true',
                    dest='all',
                    default=False,
                    help='Copy all themes'),
        make_option('-t', '--theme',
                    metavar='THEME',
                    dest='theme',
                    help='theme slug of the theme to copy'),
    )

    def log(self, msg):
        self.stdout.write(str(msg) + '\n')

    def handle(self, *args, **kwargs):
        if len(args) != 2:
            raise CommandError("Wrong number of arguments: "
                               "Please supply src and dest groups")

        if not kwargs['theme'] and not kwargs['all']:
            raise CommandError("You need to specify which themes to copy")

        try:
            src_group = Group.objects.get(slug=args[0])
            dest_group = Group.objects.get(slug=args[1])
        except Group.DoesNotExist:
            raise CommandError("One or two groups not found")

        if kwargs['all']:
            for theme in src_group.theme_set.all():
                theme.copy_to_group(dest_group)
                theme.update_theme_on_disk(collect_static=False)
                self.log('Copied theme {}'.format(theme.slug))

            return

        try:
            theme = Theme.objects.get(group=src_group, slug=kwargs['theme'])
        except Theme.DoesNotExist:
            raise CommandError("Can't find theme, check to see if it belongs "
                               "to src group")

        theme.copy_to_group(dest_group)
        theme.update_theme_on_disk(collect_static=False)
        self.log('Copied theme {}'.format(theme.slug))
