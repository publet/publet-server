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

from publet.utils import views

urlpatterns = patterns(
    '',
    url(r'^$', views.profile, name='profile'),
    url(r'^type/reader/$', views.change_account_type,
        name='change-account-type'),
    url(r'^activate/(?P<uuid>[0-9a-zA-Z]+)$', views.activate, name='activate'),
    url(r'^bulk-invite/$', views.bulk_invite, name='bulk-invite'),
    url(r'impersonate$', views.impersonate, name='impersonate')
)
