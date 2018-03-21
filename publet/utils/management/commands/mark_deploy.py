from django.core.management.base import BaseCommand
from publet.utils.metrics import Occurrence


class Command(BaseCommand):

    def handle(self, *args, **options):
        Occurrence('deploy').mark()
