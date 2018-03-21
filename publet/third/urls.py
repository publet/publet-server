from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^integration/(?P<integration_slug>[a-z0-9]+)/delete/$',
        'publet.third.views.integration_delete', name='integration-delete'),
    url(r'^integration/(?P<integration_slug>[a-z0-9]+)/$',
        'publet.third.views.integration_detail', name='integration-detail'),

    url(r'^buffer/oauth/callback', 'publet.third.views.buffer_callback',),
    url(r'^buffer/oauth/start', 'publet.third.views.buffer_start',
        name='buffer-oauth-start')
)
