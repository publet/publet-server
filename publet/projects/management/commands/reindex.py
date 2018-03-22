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
from publet.projects.models import (
    index_text_block, TextBlock,
    index_publication, Publication
)


class Command(BaseCommand):

    def handle(self, *args, **options):
        blocks = TextBlock.objects.filter(article__publication__status='live')
        publications = Publication.objects.filter(status='live')

        for b in blocks:
            index_text_block(b)

        for p in publications:
            index_publication(p)

        print 'Indexed', len(blocks), 'blocks'
        print 'Indexed', len(publications), 'publications'
