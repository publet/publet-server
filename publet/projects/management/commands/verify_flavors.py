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
from publet.projects.models import Theme


class Command(BaseCommand):

    def verify_theme(self, theme):
        flavors = theme.flavor_set.filter(name='Default')
        types = [f.type for f in flavors]

        if len(types) != len(set(types)):
            print theme.name, theme.slug, theme.pk, 'failed'

    def handle(self, *args, **kwargs):
        if len(args) == 1:
            try:
                theme = Theme.objects.get(slug=args[0])
            except Theme.DoesNotExist:
                raise CommandError("Theme doesn't exist")

            self.verify_theme(theme)
            return

        for t in Theme.objects.all():
            self.verify_theme(t)
