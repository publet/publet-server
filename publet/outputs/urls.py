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
from publet.outputs.views import (
    download_publication_html, download_publication_epub,
    download_publication_pdf, download_publication_mobi,
    preview_publication_html, render_publication_iframe,
    render_publication_frameless, publication_thumbnail, publication_heatmap
)


urlpatterns = patterns(
    '',
    url(r'^outputs/download-publication/html/(?P<publication_slug>.*).zip$',
        download_publication_html, name='download-publication-html'),
    url(r'^outputs/download-publication/epub/(?P<publication_slug>.*).epub$',
        download_publication_epub, name='download-publication-epub'),
    url(r'^outputs/download-publication/mobi/(?P<publication_slug>.*).mobi$',
        download_publication_mobi, name='download-publication-mobi'),
    url(r'^outputs/download-publication/pdf/(?P<publication_slug>.*).pdf$',
        download_publication_pdf, name='download-publication-pdf'),
    url(r'^outputs/download/article/(?P<article_slug>.*)$',
        'publet.outputs.views.protected_file', name='protected-article-file'),
    url(r'^outputs/download/publication/(?P<publication_slug>.*)$',
        'publet.outputs.views.protected_file',
        name='protected-publication-file'),
    url(r'^outputs/publication/iframe/(?P<publication_slug>.*)$',
        render_publication_iframe, name='render-publication-iframe'),
    url(r'^outputs/publication/frameless/(?P<publication_slug>.*)$',
        render_publication_frameless, name='render-publication-frameless'),
    url(r'^outputs/request/$', 'publet.outputs.views.render_request'),
    url(r'^appcache$', 'publet.outputs.views.appcache', name='appcache'),
    url(r'outputs/partials/article-(?P<article_pk>[0-9]+).html',
        'publet.outputs.views.article_partial', name='article-partial'),

    url(r'(?P<block_type>[tgav])(?P<code>[a-zA-Z0-9]+)$',
        'publet.outputs.views.short_link_redirect', name='ultra-short-link'),

    # TODO: Remove these .* regexes

    url(r'^heatmap/(?P<group_slug>.*)/(?P<publication_slug>.*)/$',
        publication_heatmap, name='publication-heatmap'),
    url(r'^heatmap/(?P<group_slug>.*)/(?P<publication_slug>.*)/(?P<page>[0-9]+)$',
        publication_heatmap, name='publication-heatmap'),
    url(r'^(?P<group_slug>.*)/(?P<publication_slug>.*)/$',
        preview_publication_html, name='preview-publication-html'),
    url(r'^thumb/(?P<group_slug>.*)/(?P<publication_slug>.*)/publication.jpg$',
        publication_thumbnail, name='publication-thumbnail'),
    url(r'^(?P<group_slug>.*)/(?P<publication_slug>.*)/(?P<page>[0-9]+)$',
        preview_publication_html, name='preview-publication-html-page'),
    url(r'^iframe/(?P<pk>[\d]+)$', 'publet.outputs.views.iframe_embed',
        name='iframe')
)
