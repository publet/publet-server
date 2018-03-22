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
from django import template


register = template.Library()


def pad(n):
    if n < 10:
        return '0' + str(n)

    return str(n)


def minutes(seconds):
    if seconds in (0, None, ''):
        return '0s'

    if isinstance(seconds, float):
        seconds = round(seconds)

    seconds = int(seconds)

    if seconds < 60:
        return str(seconds) + 's'

    over = seconds % 60
    minutes = (seconds - over) / 60

    return str(minutes) + 'min ' + str(over) + 's'


class WithFeature(template.base.Node):

    def __init__(self, nodelist, feature_slug):
        self.nodelist = nodelist
        self.feature_slug = feature_slug

    def render(self, context):
        request = context.get('request')

        if not request.is_feature_active(self.feature_slug):
            return ''

        return self.nodelist.render(context)


def with_feature(parser, token):
    _, format_string = token.split_contents()
    nodelist = parser.parse('end_with_feature')
    parser.delete_first_token()
    return WithFeature(nodelist, format_string)


register.filter('minutes', minutes)
register.tag('with_feature', with_feature)
