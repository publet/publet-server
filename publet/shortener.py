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
"""
Alternative urlconf that is used for the pblt.co domain for link
shortening
"""
from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^(?P<group_slug>.*)/(?P<publication_slug>.*)/$',
        'publet.outputs.views.preview_publication_html',
        name='preview-publication-html'),

    url(r'(?P<block_type>[tgav])(?P<code>[a-zA-Z0-9]+)',
        'publet.outputs.views.short_link_redirect', name='ultra-short-link'),
)
