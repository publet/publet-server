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
from django.conf.urls import *

from publet.payments.views import (
    downgrade, preorder, purchase, upgrade, subscribe, unsubscribe
)

urlpatterns = patterns(
    '',
    url(r'^downgrade/$', downgrade, name='payments-downgrade'),
    url(r'^preorder/(?P<group_slug>.*)/(?P<publication_slug>.*)/$', preorder,
        name='payments-preorder'),
    url(r'^purchase/(?P<group_slug>.*)/(?P<publication_slug>.*)/$', purchase,
        name='payments-purchase'),
    url(r'^upgrade/$', upgrade, name='payments-upgrade'),
    url(r'^subscribe/(?P<group_slug>.*)/$', subscribe,
        name='payments-subscribe'),
    url(r'^unsubscribe/(?P<group_slug>.*)/$', unsubscribe,
        name='payments-unsubscribe'),
)
