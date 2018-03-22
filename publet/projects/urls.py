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
from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^admin/projects/publications/change-group/(?P<pk>\d+)/$',
        'publet.projects.views.change_group_admin_view',
        name='admin-change-group'),
    url(r'^themes/$', 'publet.projects.views.theme_list',
        name='theme-list'),
    url(r'^internal/block/(?P<block_id>\d+)$',
        'publet.projects.views.internal_block_id',
        name='internal-block-id')
)
