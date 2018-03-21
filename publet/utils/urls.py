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
