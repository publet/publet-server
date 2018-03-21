from subprocess import check_output

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from annoying.functions import get_object_or_None

from publet.projects.pdf.core import parse_pdf_from_xml
from publet.projects.models import TextBlock, Publication, Article, NewArticle


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('publication_slug', type=str)
        parser.add_argument('file', type=str)
        parser.add_argument('--new', action='store_true', dest='is_new',
                            default=False)

    def handle_new(self, publication, blocks, name):
        article = NewArticle(publication=publication, name=name,
                             created_by=publication.created_by)
        article.data = article.default_data

        text_blocks = []

        for block in blocks:
            text = ''.join([text.text for text in block])
            text_blocks.append({
                "classes": [],
                "content": {
                    "style": 'paragraph',
                    "text": text
                },
                "type": "TextBlock"
            })

        article.data['sections'][0]['layout'] = 'OneCol'
        article.data['sections'][0]['columns'] = [
            text_blocks
        ]

        article.save()

    def handle(self, *args, **options):
        publication = get_object_or_None(Publication,
                                         slug=options['publication_slug'])

        if not publication:
            raise CommandError('Publication not found')

        out = check_output(
            'pdftohtml -xml -i -stdout {}'.format(options['file']),
            shell=True)

        blocks, default_font = parse_pdf_from_xml(out)

        if options['is_new']:
            assert publication.new_style
            return self.handle_new(publication, blocks, options['file'])

        with transaction.atomic():
            article = Article.objects.create(name=options['file'],
                                             publication=publication)

            i = 0

            for block in blocks:
                text = ''.join([text.text for text in block])
                TextBlock.objects.create(content=text, article=article,
                                         order=i)
                i += 1

                # Separator
                TextBlock.objects.create(content='\n\n', article=article,
                                         order=i)
                i += 1
