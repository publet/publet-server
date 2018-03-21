from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^$', 'publet.docs.views.index', name='docs-index'),
    url(r'^(?P<section>[a-zA-Z-]+)/(?P<slug>[a-zA-Z0-9-]+)/$',
        'publet.docs.views.single', name='docs-single')
)
