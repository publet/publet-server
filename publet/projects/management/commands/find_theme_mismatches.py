"""
Publet
Copyright (C) 2018  Publet Inc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
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
