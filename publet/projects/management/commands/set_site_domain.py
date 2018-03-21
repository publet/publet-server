from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('site_name', type=str)

    def handle(self, *args, **options):
        s = Site.objects.all()[0]
        s.domain = options['site_name']
        s.save()
