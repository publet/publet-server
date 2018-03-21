from django.conf.urls import *

from publet.payments.views import (
    downgrade, preorder, purchase, upgrade, subscribe, unsubscribe
)

urlpatterns = patterns(
    '',
    url(r'^downgrade/$', downgrade, name='payments-downgrade'),
    url(r'^preorder/(?P<group_slug>.*)/(?P<publication_slug>.*)/$', preorder,
        name='payments-preorder'),
    url(r'^purchase/(?P<group_slug>.*)/(?P<publication_slug>.*)/$', purchase,
        name='payments-purchase'),
    url(r'^upgrade/$', upgrade, name='payments-upgrade'),
    url(r'^subscribe/(?P<group_slug>.*)/$', subscribe,
        name='payments-subscribe'),
    url(r'^unsubscribe/(?P<group_slug>.*)/$', unsubscribe,
        name='payments-unsubscribe'),
)
