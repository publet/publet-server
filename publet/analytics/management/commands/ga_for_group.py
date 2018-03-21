from django.core.management.base import BaseCommand, CommandError
from publet.groups.models import Group
from publet.analytics.analytics import get_all_metrics_for_group


class Command(BaseCommand):

    args = 'group_pk'

    def handle(self, *args, **kwargs):
        if len(args) != 1:
            raise CommandError('Needs exactly one group pk')

        group = Group.objects.get(pk=args[0])
        print get_all_metrics_for_group(group)
