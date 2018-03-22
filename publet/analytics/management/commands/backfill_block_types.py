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
from publet.projects.models import (
    TextBlock, PhotoBlock, AudioBlock, VideoBlock, PublicationSocialGateEntry
)


class Command(BaseCommand):

    def find_block(self, pk):
        return (
            get_object_or_None(TextBlock, pk=pk) or
            get_object_or_None(PhotoBlock, pk=pk) or
            get_object_or_None(AudioBlock, pk=pk) or
            get_object_or_None(VideoBlock, pk=pk)
        )

    def handle(self, *args, **kwargs):
        with_block_id = Event.objects.filter(block_id__isnull=False,
                                             block_type='')
        gates = PublicationSocialGateEntry.objects.filter(block_type='')

        objs = list(with_block_id) + list(gates)

        dangling = 0

        for obj in objs:
            block = self.find_block(obj.block_id)

            if not block:
                dangling += 1
                continue

            obj.block_type = block.type
            obj.save()

        print 'Done; dangling: {}'.format(dangling)
