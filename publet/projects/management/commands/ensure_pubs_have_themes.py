from django.core.management.base import BaseCommand
from publet.projects.models import Publication


class Command(BaseCommand):

    def log(self, msg):
        self.stdout.write(str(msg) + '\n')

    def handle(self, *args, **kwargs):
        themeless = Publication.objects.filter(theme__isnull=True)

        if not themeless:
            return

        self.log(str(themeless.count()) + ' to process')

        for pub in themeless:
            self.log(pub.slug)
            default_theme = pub.group.theme_set.get(name='Default')
            pub.theme = default_theme
            pub.save()
