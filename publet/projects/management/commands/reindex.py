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
