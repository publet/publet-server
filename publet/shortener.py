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
