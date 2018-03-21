from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^hourly$', 'publet.metrics.views.hourly', name='metrics-hourly'),
    url(r'^daily$', 'publet.metrics.views.daily', name='metrics-daily'),
    url(r'^db$', 'publet.metrics.views.db', name='metrics-db'),
    url(r'^celery$', 'publet.metrics.views.celery_queue_size',
        name='celery-queue-size')
)
