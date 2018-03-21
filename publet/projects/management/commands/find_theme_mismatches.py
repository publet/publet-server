from optparse import make_option
from django.core.management.base import BaseCommand
from publet.projects.models import Publication


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--fix',
                    action='store_true',
                    dest='fix',
                    default=False,
                    help='Fix as well?'),)

    def handle(self, *args, **kwargs):
        ok = []
        fail = []

        for pub in Publication.objects.all():
            if pub.theme in pub.group.theme_set.all():
                ok.append(pub)
            else:
                fail.append(pub)

        print len(fail), 'publications to fix'

        if not kwargs['fix']:
            return

        print 'Fixing...'

        for pub in fail:
            print pub.slug
            theme = pub.theme
            group = pub.group

            group_theme_names = [t.name for t in group.theme_set.all()]

            if theme.name in group_theme_names:
                pub.theme = group.theme_set.get(name=pub.theme.name)
                pub.save()
                continue

            pub.theme = group.theme_set.get(name='Default')
            pub.save()
