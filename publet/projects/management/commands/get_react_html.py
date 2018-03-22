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
from publet.projects.models import NewArticle, render_article
from publet.projects.react import get_article_html, get_article_document


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('article_id', type=int)

    def handle(self, *args, **options):
        instance = get_object_or_None(NewArticle, pk=options['article_id'])

        if not instance:
            raise CommandError('Article not found')

        article = render_article(instance)
        article = get_article_html(article)
        get_article_document(instance, article)
