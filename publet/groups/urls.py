from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^$', 'publet.groups.views.groups_list', name='groups-list'),

    url(r'^(?P<group_slug>.*)/integrations/$',
        'publet.groups.views.integrations',
        name='integrations'),

    url(r'^(?P<group_slug>.*)/members/add/$',
        'publet.groups.views.members_add',
        name='group-members-add'),

    url(r'^(?P<group_slug>.*)/members/$',
        'publet.groups.views.members',
        name='group-members'),

    url(r'^(?P<group_slug>.*)/members/'
        '(?P<member_pk>[0-9]+)/delete/$',
        'publet.groups.views.delete_member',
        name='group-members-delete'),

    url(r'^(?P<group_slug>.*)/members/'
        '(?P<member_pk>[0-9]+)/change/$',
        'publet.groups.views.change_member',
        name='group-members-change'),

    url(r'^(?P<group_slug>.*)/hubs/edit/(?P<hub_slug>[a-zA-Z0-9-]+)/$',
        'publet.groups.views.hub_detail',
        name='group-hub-detail'),

    url(r'^(?P<group_slug>.*)/hubs/add/$',
        'publet.groups.views.hubs_add',
        name='group-hubs-add'),

    url(r'^(?P<group_slug>.*)/hubs/(?P<hub_slug>[a-zA-Z0-9-]+)/delete/$',
        'publet.groups.views.hub_delete',
        name='group-hub-delete'),

    url(r'^(?P<group_slug>.*)/hubs/(?P<hub_slug>[a-zA-Z0-9-]+)/$',
        'publet.groups.views.hub_live',
        name='group-hub-live'),

    url(r'^(?P<group_slug>.*)/hubs/(?P<hub_slug>[a-zA-Z0-9-]+)/search/$',
        'publet.groups.views.hub_live_search',
        name='group-hub-live-search'),

    url(r'^(?P<group_slug>.*)/hubs/$',
        'publet.groups.views.hubs',
        name='group-hubs'),

    url(r'^(?P<group_slug>.*)/publications/(?P<publication_slug>.*)/'
        'articles/(?P<article_slug>.*)/$',
        'publet.projects.views.article_detail', name='article-detail'),
    url(r'^(?P<group_slug>.*)/publications/(?P<publication_slug>.*)/data/$',
        'publet.projects.views.publication_detail_data',
        name='publication-detail-data'),
    url(r'^(?P<group_slug>.*)/publications/(?P<publication_slug>.*)/csv/$',
        'publet.projects.views.publication_conversions_csv_download',
        name='publication-csv-export'),
    url(r'^(?P<group_slug>.*)/publications/(?P<publication_slug>.*)/$',
        'publet.projects.views.publication_detail',
        name='publication-detail'),
    url(r'^(?P<group_slug>.*)/themes/$',
        'publet.projects.views.group_theme_list',
        name='group-theme-list'),
    url(r'^(?P<group_slug>.*)/themes/(?P<theme_slug>.*)/$',
        'publet.projects.views.theme_detail',
        name='theme-detail'),
    url(r'^(?P<group_slug>.*)/publications/(?P<publication_slug>.*)/'
        'articles/(?P<article_slug>.*)/draft$',
        'publet.projects.views.article_draft',
        name='article-draft'),

    url(r'^(?P<group_slug>.*)/$',
        'publet.groups.views.group_detail',
        name='group-detail'),
)
