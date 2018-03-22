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
