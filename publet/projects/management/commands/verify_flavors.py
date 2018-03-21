from django.core.management.base import BaseCommand, CommandError
from publet.projects.models import Theme


class Command(BaseCommand):

    def verify_theme(self, theme):
        flavors = theme.flavor_set.filter(name='Default')
        types = [f.type for f in flavors]

        if len(types) != len(set(types)):
            print theme.name, theme.slug, theme.pk, 'failed'

    def handle(self, *args, **kwargs):
        if len(args) == 1:
            try:
                theme = Theme.objects.get(slug=args[0])
            except Theme.DoesNotExist:
                raise CommandError("Theme doesn't exist")

            self.verify_theme(theme)
            return

        for t in Theme.objects.all():
            self.verify_theme(t)
