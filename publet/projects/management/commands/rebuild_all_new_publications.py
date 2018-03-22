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
from django.core.management.base import BaseCommand
from publet.projects.models import Publication
from publet.projects.tasks import upload_new_publication


class Command(BaseCommand):

    def handle(self, *args, **options):
        publications = Publication.objects.filter(
            new_style=True).order_by('-modified')

        for p in publications:
            upload_new_publication.delay(p.pk)

        print '{} publications scheduled for rebuilding'.format(
            publications.count())
