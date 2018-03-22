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
from django_rq import job
# from celery.task import periodic_task
# from celery.schedules import crontab
# from django.contrib.auth import get_user_model
# from metrics import Gauge
# from publet.projects.models import Publication, Article
# from publet.analytics.models import Event
# from publet.utils.utils import get_disk_stats, get_cpu_usage


# @periodic_task(run_every=crontab())
# def gauge_users():
#     count = get_user_model().objects.all().count()
#     Gauge('users-count').report(count)


# @periodic_task(run_every=crontab())
# def gauge_publications():
#     all = Publication.objects.all().count()
#     live = Publication.objects.filter(status='live').count()

#     Gauge('publications-live-count').report(live)
#     Gauge('publications-count').report(all)


# @periodic_task(run_every=crontab())
# def gauge_articles():
#     count = Article.objects.all().count()
#     Gauge('articles-count').report(count)


# @periodic_task(run_every=crontab())
# def gauge_events():
#     count = Event.objects.all().count()
#     Gauge('events-count').report(count)


# @periodic_task(run_every=crontab())
# def gauge_disk_usage():
#     stats = get_disk_stats()
#     Gauge('disk.used-percent').report(stats['used_percent'])


# @periodic_task(run_every=crontab())
# def gauge_cpu_usage():
#     cpu = get_cpu_usage()
#     Gauge('cpu-usage').report(cpu)


@job
def fail_task():
    raise Exception('Test failed')


@job
def process_signup_notification(signup_id):
    from publet.utils.models import Signup

    s = Signup.objects.get(pk=signup_id)

    try:
        s.submit_to_close()
    except:
        return

    s.send_slack_message()
