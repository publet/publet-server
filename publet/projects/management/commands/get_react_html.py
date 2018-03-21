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
