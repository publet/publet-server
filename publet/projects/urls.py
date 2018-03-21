from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^admin/projects/publications/change-group/(?P<pk>\d+)/$',
        'publet.projects.views.change_group_admin_view',
        name='admin-change-group'),
    url(r'^themes/$', 'publet.projects.views.theme_list',
        name='theme-list'),
    url(r'^internal/block/(?P<block_id>\d+)$',
        'publet.projects.views.internal_block_id',
        name='internal-block-id')
)
