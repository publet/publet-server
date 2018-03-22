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
from django.conf.urls import patterns, url, include

from publet.projects.api import (
    GroupResource, ArticleResource, ThemeResource, PhotoBlockResource,
    TypeResource, TextBlockResource, VideoBlockResource, AudioBlockResource,
    GroupMemberResource, UserResource, PublicationResource, FontResource,
    ColorResource, PresetResource, FlatPublicationResource,
    PhotoResource, AssetResource, FontFileResource, FlavorResource,
    FullFlavorResource, FlatArticleResource,
    PublicationWithFlatArticlesResource, BrokerPublicationResource,
    PublicationSocialGateEntryResource, GatePublicationResource,
    PDFUploadResource, FeedbackResource,
    GenericGateResource, FlatNewArticleResource,
    PublicationWithFlatNewArticlesResource
)


user_resource = UserResource()
group_resource = GroupResource()
groupmember_resource = GroupMemberResource()

publication_resource = PublicationResource()
flat_publication_resource = FlatPublicationResource()
publication_with_flat_articles_resource = PublicationWithFlatArticlesResource()
publication_with_flat_new_articles_resource = \
    PublicationWithFlatNewArticlesResource()
broker_publication = BrokerPublicationResource()

article_resource = ArticleResource()
flat_article_resource = FlatArticleResource()
flat_new_article_resource = FlatNewArticleResource()

type_resource = TypeResource()
preset_resource = PresetResource()
theme_resource = ThemeResource()

photoblock_resource = PhotoBlockResource()
textblock_resource = TextBlockResource()
videoblock_resource = VideoBlockResource()
audioblock_resource = AudioBlockResource()
font_resource = FontResource()
fontfile_resource = FontFileResource()
color_combination_resource = ColorResource()
photo_resource = PhotoResource()
asset_resource = AssetResource()
flavor_resource = FlavorResource()
full_flavor_resource = FullFlavorResource()

publication_social_gate_entry_resource = PublicationSocialGateEntryResource()
gate_publication_resource = GatePublicationResource()
generic_gate_resource = GenericGateResource()
pdf_resource = PDFUploadResource()
feedback_resource = FeedbackResource()

from publet.projects.rest import (
    GroupResource, PublicationResource, PublicationCollectionResource,
    ArticleResource, AuthService, ArticleCollectionResource, ThemeFontResource,
    ThemeResource, FilePickerPolicyResource, UserResource
)


urlpatterns = patterns(
    '',

    url(r'^article-name/(?P<publication_id>[0-9]+)/(?P<article_id>[0-9]+)/$',
        'publet.projects.api.article_name'),
    url(r'^2/auth/', AuthService.as_view(), name='auth-service'),
    url(r'^2/user/$', UserResource.as_view(), name='user-service'),
    url(r'^2/filepicker/', FilePickerPolicyResource.as_view(),
        name='filepicker-service'),

    url(r'^2/group/(?P<id>[0-9]+)/$',
        GroupResource.as_view(),
        name='api-group-detail'),

    url(r'^2/group/(?P<id>[0-9]+)/publications/$',
        PublicationCollectionResource.as_view(),
        name='api-publication-detail'),
    url(r'^2/publication/(?P<pk>[0-9]+)/$', PublicationResource.as_view(),
        name='api-publication-detail'),

    url(r'^2/publication/(?P<id>[0-9]+)/articles/$',
        ArticleCollectionResource.as_view(), name='api-article-detail'),

    url(r'^2/article/(?P<pk>[0-9]+)/$', ArticleResource.as_view(),
        name='api-article-detail'),

    url(r'^2/theme/(?P<pk>[0-9]+)/fonts.css$', ThemeFontResource.as_view(),
        name='api-theme-font-detail'),

    url(r'^2/theme/(?P<pk>[0-9]+)/$', ThemeResource.as_view(),
        name='api-theme-detail'),

    # TASTYPIE

    url(r'^user/identity/$', 'publet.projects.views.user_identity',
        name='identity'),
    url(r'^user/basic-and-pro/',
        'publet.projects.views.user_basic_and_pro'),
    # NOTE the user_resource URLs are completely inaccessible, but tastypie
    # needs them anyway.
    url(r'^', include(user_resource.urls)),

    url(r'^group/(?P<group_pk>[0-9]+)/hub/(?P<hub_pk>[0-9]+)/search/',
        'publet.groups.views.search_group_api'),

    url(r'^', include(group_resource.urls)),
    url(r'^', include(groupmember_resource.urls)),

    url(r'^publication/(?P<publication_pk>[0-9]+)/reorder/',
        'publet.projects.views.reorder_publication'),
    url(r'^publication/(?P<publication_pk>[0-9]+)/duplicate/',
        'publet.projects.views.duplicate_publication'),
    url(r'^publication/(?P<publication_pk>[0-9]+)/republish/',
        'publet.projects.views.republish_publication'),

    url(r'^', include(publication_resource.urls)),
    url(r'^', include(flat_publication_resource.urls)),
    url(r'^', include(publication_with_flat_articles_resource.urls)),
    url(r'^', include(publication_with_flat_new_articles_resource.urls)),
    url(r'^', include(broker_publication.urls)),
    url(r'^', include(flat_article_resource.urls)),
    url(r'^', include(flat_new_article_resource.urls)),

    url(r'^article/(?P<article_pk>[0-9]+)/reorder/',
        'publet.projects.views.reorder_article'),
    url(r'^', include(article_resource.urls)),

    url(r'^', include(type_resource.urls)),
    url(r'^', include(preset_resource.urls)),
    url(r'^', include(theme_resource.urls)),

    # Content
    url(r'^', include(font_resource.urls)),
    url(r'^', include(fontfile_resource.urls)),
    url(r'^', include(color_combination_resource.urls)),
    url(r'^', include(flavor_resource.urls)),
    url(r'^', include(full_flavor_resource.urls)),

    # Blocks
    url(r'^', include(photoblock_resource.urls)),
    url(r'^', include(textblock_resource.urls)),
    url(r'^', include(videoblock_resource.urls)),
    url(r'^', include(audioblock_resource.urls)),

    url(r'^', include(photo_resource.urls)),
    url(r'^', include(asset_resource.urls)),

    url(r'^', include(publication_social_gate_entry_resource.urls)),
    url(r'^', include(gate_publication_resource.urls)),
    url(r'^', include(generic_gate_resource.urls)),
    url(r'^', include(pdf_resource.urls)),
    url(r'^', include(feedback_resource.urls)),

    url(r'^chrome-extension$',
        'publet.projects.views.chrome_extension',
        name='chrome-extension'),
    url(r'^readability/(?P<pk>\d+)$',
        'publet.projects.views.readability',
        name='readability'),
    url(r'^integration-submission/(?P<block_type>text|photo|audio|video)'
        'block/(?P<block_id>[0-9]+)/$',
        'publet.projects.views.integration_submission_handler'),
)
