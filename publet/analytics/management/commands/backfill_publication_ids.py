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
from annoying.functions import get_object_or_None
from publet.analytics.models import Event
from publet.projects.models import Article


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        without_publication_id = Event.objects.filter(
            publication_id__isnull=True, article_id__isnull=False)

        for event in without_publication_id:
            article = get_object_or_None(Article, pk=event.article_id)

            if not article:
                print 'Skipping event {}...'.format(event.pk)
                continue

            event.publication_id = article.publication.pk
            event.save()
