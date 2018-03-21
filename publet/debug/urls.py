from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url('^$', 'publet.debug.views.home', name='debug-list'),
    url('^404$', 'publet.debug.views.handle_404', name='debug-404'),
    url('^500$', 'publet.debug.views.handle_500', name='debug-500')
)
