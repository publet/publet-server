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
from django.conf import settings
from django.conf.urls import patterns, include, url, handler404
from django.contrib import admin
from django.http import HttpResponseRedirect
from publet.groups.views import profile_detail
from utils.views import PubletRegistrationView

admin.autodiscover()

urlpatterns = patterns(
    '',

    url(r'apple-touch-icon.png', handler404),
    url(r'apple-touch-icon-precomposed.png', handler404),
    url(r'wp-login.php', handler404),

    url(r'^django-rq/', include('django_rq.urls')),

    # Admin
    url(r'^signup.html$', 'publet.utils.views.signup_form',
        name='signup-form'),
    url(r'^email$', 'publet.utils.views.publet_sign_up_handler'),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^metrics/', include('publet.metrics.urls')),
    url(r'^docs/', include('publet.docs.urls')),
    url(r'^embed/$', 'publet.utils.views.embed_test'),

    # Third party, OAuth callbacks, etc
    url('^third/', include('publet.third.urls')),

    # Pages
    url(r'^$', 'publet.views.home', name='home'),
    url(r'^styleguide/$', 'publet.views.styleguide', name='styleguide'),

    # Apps
    url(r'^', include('publet.projects.urls')),
    url(r'^groups/', include('publet.groups.urls')),
    url(r'^payments/', include('publet.payments.urls')),
    url(r'^account/', include('publet.utils.urls')),
    url(r'^', include('publet.reader.urls')),

    url(r'^api/', include('publet.projects.api_urls')),

    # Registration
    url(r'', include('registration.backends.default.urls')),
    url(r'^register/$', lambda x: HttpResponseRedirect('/signup/')),
    url(r'^signup/$', PubletRegistrationView.as_view(),
        name='registration_register'),

    url(r'^email/change/$', 'publet.utils.views.change_email',
        name='change-email'),

    # Debug
    url(r'^_debug/', include('publet.debug.urls')),

    # Outputs
    url(r'^', include('publet.outputs.urls')),

    # Profile
    url(r'^(?P<profile_slug>.*)/$', profile_detail, name='profile-detail'),
    url(r'^(?P<path>.*)', 'publet.outputs.views.custom_publication_resource'),
)

if settings.DEBUG:
    urlpatterns += patterns('django.contrib.staticfiles.views',
                            url(r'^static/(?P<path>.*)$', 'serve'),
                            url(r'^media/(?P<path>.*)$', 'serve'),
                            )
