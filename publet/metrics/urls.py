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
    url(r'^hourly$', 'publet.metrics.views.hourly', name='metrics-hourly'),
    url(r'^daily$', 'publet.metrics.views.daily', name='metrics-daily'),
    url(r'^db$', 'publet.metrics.views.db', name='metrics-db'),
    url(r'^celery$', 'publet.metrics.views.celery_queue_size',
        name='celery-queue-size')
)
