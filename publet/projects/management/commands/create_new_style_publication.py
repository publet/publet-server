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
from publet.groups.models import Group
from publet.projects.models import Publication, NewArticle


article = {
    "created": "2015-07-27T14:35:13.918069",
    "id": 3003,
    "modified": "2015-07-27T14:35:13.918095",
    "name": "New style article",
    "sections": [
        {
            "bgImageUrl": None,
            "columns": [
                [
                    {
                        "classes": [],
                        "content": {
                            "alt": None,
                            "caption": "Hello caption",
                            "description": None,
                            "height": 294,
                            "id": 9847,
                            "style": None,
                            "url": "http://i.imgur.com/W5WkHF5.jpg?signature=9a800a1507049e983e3c39198072b927979cdacaf89b7c237f8f283de1e5667c&policy=eyJjYWxsIjogWyJyZWFkIiwgImNvbnZlcnQiXSwgImV4cGlyeSI6ICIyNTI0NjQwNDAwIn0=",
                            "width": 420
                        },
                        "created": "2015-07-27T14:35:14.211325",
                        "id": 6584,
                        "modified": "2015-07-27T14:35:14.211351",
                        "type": "ImageBlock"
                    },
                    {
                        "classes": [],
                        "content": {
                            "style": None,
                            "text": "First column, second block"
                        },
                        "created": "2015-07-27T14:35:14.159686",
                        "id": 23601,
                        "modified": "2015-07-27T14:35:14.159709",
                        "type": "TextBlock"
                    },
                    {
                        "classes": [],
                        "content": {
                            "style": None,
                            "text": "First column, first block"
                        },
                        "created": "2015-07-27T14:35:14.101654",
                        "id": 23600,
                        "modified": "2015-07-27T14:35:14.101679",
                        "type": "TextBlock"
                    }
                ],
                [
                    {
                        "classes": [],
                        "content": {
                            "style": None,
                            "text": "Second column, first block"
                        },
                        "created": "2015-07-27T14:35:14.273059",
                        "id": 23602,
                        "modified": "2015-07-27T14:35:14.273075",
                        "type": "TextBlock"
                    }
                ]
            ],
            "id": 1,
            "layout": "TwoCol",
            "style": {}
        }
    ]
}


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('group_slug', type=str)

    def handle(self, *args, **options):
        group = get_object_or_None(Group, slug=options['group_slug'])

        if not group:
            raise CommandError('Group not found')

        p = Publication.objects.create(name='New style publication',
                                       new_style=True, group=group)
        NewArticle.objects.create(publication=p, data=article)
