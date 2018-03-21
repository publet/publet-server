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
