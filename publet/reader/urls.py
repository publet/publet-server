from django.conf.urls import patterns, url
from publet.reader.views import dashboard, featured


urlpatterns = patterns(
    '',
    url(r'^dashboard/$', dashboard, name='reader-dashboard'),
    url(r'^featured/$', featured, name='reader-featured'),
)
