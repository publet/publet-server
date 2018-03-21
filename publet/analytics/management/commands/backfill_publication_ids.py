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
