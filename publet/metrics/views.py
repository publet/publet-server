import json
import redis
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model

from publet.analytics.models import Event
from publet.groups.models import Group

r = redis.StrictRedis(db=0)

INSTALLATION = getattr(settings, 'INSTALLATION', 'staging')


METRICS = (
    ('all-hosts.response-time.value.95',),
    ('all-hosts.site-sections.api-response-time.value.95',),
    ('all-hosts.requests.completed.rate-per-second',),
    ('all-hosts.gauges.users-count',),
    ('all-hosts.gauges.publications-count',),
    ('all-hosts.gauges.articles-count',),
    ('all-hosts.gauges.events-count',),
    ('all-hosts.gauges.disk.used-percent', 'all-hosts.gauges.cpu-usage',),
)


def show_metrics(request, hours):
    return render(request, 'metrics/dashboard.html', {
        'INSTALLATION': INSTALLATION,
        'metrics': METRICS,
        'hours': hours
    })


@user_passes_test(lambda u: u.is_superuser)
def hourly(request):
    return show_metrics(request, 1)


@user_passes_test(lambda u: u.is_superuser)
def daily(request):
    return show_metrics(request, 24)


@user_passes_test(lambda u: u.is_superuser)
def db(request):
    eo = Event.objects

    unique_per_pub = eo.get_global_unique_visitors_per_publication()
    engaged_per_pub = eo.global_average_engaged_time_per_publication()
    engaged_per_art = eo.global_average_engaged_time_per_article()
    engaged_per_pub_user = \
        eo.global_average_engaged_time_per_publication_per_user()
    engaged_per_art_user = \
        eo.global_average_engaged_time_per_article_per_user()
    social = eo.get_global_social_data()

    all_users = get_user_model().objects.all().count()

    active_users = eo.get_num_active_users()
    inactive_users = all_users - active_users

    active_user_ratio = active_users / (all_users / 100.0)
    weekly_logins = eo.weekly_average_logins_per_user()

    avg_publications_per_group = Group.objects.average_publications_per_group()

    return render(request, 'metrics/db.html', {
        'global': {
            'unique_per_publication': unique_per_pub,
            'engaged_per_pub': engaged_per_pub,
            'engaged_per_pub_user': engaged_per_pub_user,
            'engaged_per_art': engaged_per_art,
            'engaged_per_art_user': engaged_per_art_user,
            'social': social,
        },
        'users': {
            'all_users': all_users,
            'active_users': active_users,
            'active_user_ratio': active_user_ratio,
            'inactive_users': inactive_users,
            'weekly_logins': weekly_logins
        },
        'publications': {
            'avg_per_group': avg_publications_per_group
        }
    })


@user_passes_test(lambda u: u.is_superuser)
def celery_queue_size(request):
    data = {
        'size': r.llen('celery')
    }
    return HttpResponse(json.dumps(data), content_type='application/json')
