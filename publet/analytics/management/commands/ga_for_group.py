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
