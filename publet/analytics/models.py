import json
from functools import partial
from itertools import groupby
from datetime import datetime, timedelta
from django.conf import settings
from django.db import models, connection, connections
from django.db.utils import ConnectionDoesNotExist
from django.contrib.auth import get_user_model
from publet.utils.metrics import Timer
from publet.utils.fn import merge
from publet.common.templatetags.common_tags import minutes


TRACKING_SESSION_LENGTH = getattr(settings, 'TRACKING_SESSION_LENGTH', 30 * 60)
GEO_DB_NAME = getattr(settings, 'GEO_DB_NAME', 'geo')


def get_location_for_ip_int(ipint):
    query = """
    select
        city_locations.continent_name,
        city_locations.country_name,
        city_locations.subdivision_1_name,
        city_locations.city_name
    from
        city_blocks
    join city_locations on city_locations.geoname_id = city_blocks.geoname_id
    where
        network <= %s
    order by network desc
    limit 1;
    """
    with Timer('sql.location'):
        try:
            cursor = connections['geo'].cursor()
        except ConnectionDoesNotExist:
            return None

        cursor.execute(query, [ipint])
        row = cursor.fetchone()

        if not row:
            return

        row = dict(zip(['continent', 'country', 'region', 'city'], row))

    return row


def get_date_range(start, end):
    start = start.date()
    end = end.date()

    dates = [start]
    now = start

    while True:
        now = now + timedelta(days=1)
        dates.append(now)

        if now == end:
            break

    return dates


def has_session_reached_path(path, session):
    return session.has_reached_path(path)


def dictfetchall(cursor):
    """
    Returns all rows from a cursor as a dict

    Taken from:

    https://docs.djangoproject.com/en/1.7/topics/db/sql/
    """
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


class HeatmapItem(object):

    def __init__(self, seconds, percent):
        self.seconds = seconds
        self.percent = percent
        self.luminosity = None

    def css(self, alpha=0.75):
        if not self.percent:
            value = 0
            alpha = 0
        else:
            if not self.luminosity:
                self.luminosity = self.scale(self.percent)

            value = self.luminosity

        return "background-color: hsla(0, 100%, {}%, {});".format(value, alpha)

    def scale(self, n, f=50):
        """
        E.g. 50% points in the middle of the scale
        """
        n = 100 - n
        ratio = 100.0 / f
        new_n = n / ratio
        offset = (100.0 - f) / 2.0
        return new_n + offset

    def serialize(self):
        return {
            'percent': self.percent,
            'css': self.css(),
            'seconds': self.seconds,
            'seconds_formatted': minutes(self.seconds)
        }

    def json(self):
        return json.dumps(self.serialize())


class AnalyticsSession(object):

    def __init__(self, rows=None):
        if rows:
            self.rows = rows
            self.user = self.rows[0]['anonymous_id']
        else:
            self.rows = []
            self.user = None

    def __nonzero__(self):
        return True if self.rows else False

    def __len__(self):
        return len(self.rows)

    def __iter__(self):
        return iter(self.rows)

    def append(self, row):
        self.rows.append(row)

    def has_reached_path(self, path):
        for event in self.rows:
            if event['url'] == path:
                return True

    def date(self):
        if not self.rows:
            raise Exception('Cannot get date for empty session')

        return self.rows[0]['created']

    def date_key(self):
        return self.date().strftime('%Y-%m-%d')


class EventManager(models.Manager):

    def daily_average_publication_engaged_time(self, publication_id, days=30):
        query = """
        with filled_dates as (
            select day, 0 as blank_count
            from generate_series('now'::date - '%s days'::interval,
                                 current_date::date, '1 day') as day
        ),
        for_pub as (
            select * from analytics_event
                where publication_id = %s
                    and type = 'engaged_publication'
        ),
        sec_avgs as (
            select date_trunc('day', created) as day, avg(seconds) as secs
                from for_pub
            group by date_trunc('day', created)
        )
        select filled_dates.day,
            coalesce(sec_avgs.secs, filled_dates.blank_count) as signups
        from filled_dates
            left outer join sec_avgs on sec_avgs.day = filled_dates.day
        order by filled_dates.day;"""

        with Timer('sql.average-daily-engaged-time.publication'):
            cursor = connection.cursor()
            cursor.execute(query, [days, publication_id])
            rows = cursor.fetchall()

        return rows

    def daily_average_article_engaged_time(self, article_id, days=30):
        query = """
        with filled_dates as (
            select day, 0 as blank_count
                from generate_series('now'::date - '%s days'::interval,
                                     current_date::date, '1 day') as day
        ),
        for_article as (
            select * from analytics_event where article_id = %s
        ),
        sec_avgs as (
            select date_trunc('day', created) as day, avg(seconds) as secs
                from for_article
            group by date_trunc('day', created)
        )
        select filled_dates.day,
            coalesce(sec_avgs.secs, filled_dates.blank_count) as signups
        from filled_dates
            left outer join sec_avgs on sec_avgs.day = filled_dates.day
        order by filled_dates.day;"""
        with Timer('sql.average-daily-engaged-time.article'):
            cursor = connection.cursor()
            cursor.execute(query, [days, article_id])
            rows = cursor.fetchall()

        return rows

    def get_per_block_engaged_data(self, publication_id, days=30):
        query = """
        select block_id,sum(seconds) from analytics_event
            where publication_id = %s
                and type = 'engaged_block'
                and created > 'now'::date - '%s days'::interval
            group by block_id
            order by block_id;
        """

        with Timer('sql.per-block-engaged-data'):
            cursor = connection.cursor()
            cursor.execute(query, [publication_id, days])
            rows = cursor.fetchall()

        return rows

    def get_per_block_engaged_data_normalized(self, publication_id, days=30):
        """
        Same as ``get_per_block_engaged_data`` except values are in %
        """
        rows = self.get_per_block_engaged_data(publication_id, days)

        if not rows:
            return rows

        max_value = max([r[1] for r in rows])

        def to_percent(row):
            if row[1] == max_value:
                value = 100.00
            else:
                value = float(row[1]) / float(max_value) * 100

            return (row[0], row[1], value,)

        return map(to_percent, rows)

    def get_per_block_engaged_data_with_colors(self, publication_id, days=30):
        rows = self.get_per_block_engaged_data_normalized(publication_id, days)

        def make_heatmap_item(row):
            return (row[0], HeatmapItem(row[1], row[2]))

        return map(make_heatmap_item, rows)

    def social_share_pagecount(self, publication_id, social):
        return self.filter(publication_id=publication_id, type='page',
                           social_referrer=social).count()

    def get_global_social_data(self):
        query = """
        select social_referrer,count(*) from analytics_event
          where
            social_referrer != '' and type = 'page'
            group by social_referrer;
        """
        with Timer('sql.global-social-data'):
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        return rows

    def get_social_data(self, publication_id, days=30):
        query = """
        select social_referrer,count(*) from analytics_event
          where
            social_referrer != ''
              and publication_id = %s
              and created > 'now'::date - '%s days'::interval
              and type = 'page'
            group by social_referrer;
        """
        with Timer('sql.social-data'):
            cursor = connection.cursor()
            cursor.execute(query, [publication_id, days])
            rows = cursor.fetchall()

        return rows

    def get_social_data_per_block(self, publication_id, days=30):
        query = """
        select block_id,block_type,social_referrer,count(*) from
                                                                analytics_event
          where
            social_referrer != ''
              and publication_id = %s
              and block_id is not null
              and created > 'now'::date - '%s days'::interval
              and type = 'page'
            group by block_id, block_type, social_referrer
            order by block_id;
        """
        with Timer('sql.social-data-per-block'):
            cursor = connection.cursor()
            cursor.execute(query, [publication_id, days])
            rows = cursor.fetchall()

        result = []

        for block_id, block_values in groupby(rows, key=lambda x: x[0]):
            clean = []

            for _, type, referrer, num in block_values:
                clean.append((referrer, num,))

            obj = {
                'values': dict(clean),
                'id': block_id,
                'type': type
            }

            result.append((block_id, obj,))

        return dict(result)

    def get_global_unique_visitors_per_publication(self):
        query = """
        with publications_with_users as (
            select distinct publication_id,anonymous_id from analytics_event
                where type = 'page' order by publication_id)

        select publication_id,count(publication_id)
            from publications_with_users
                group by publication_id
                order by publication_id;
        """
        with Timer('sql.analytics.global-per-pub-unique-visitors'):
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        return rows

    def get_unique_visitors(self, publication, days=30):
        query = """
        with distinct_entries as (
            select distinct on (anonymous_id) anonymous_id
            from analytics_event
                where
                    publication_id = %s
                    and type = 'page'
                    and created > 'now'::date - '%s days'::interval
        )
        select count(*) from distinct_entries;
        """
        with Timer('sql.analytics.unique-visitors'):
            cursor = connection.cursor()
            cursor.execute(query, [publication.id, days])
            rows = cursor.fetchone()
            if rows:
                rows = rows[0]

        return rows

    def get_sessions(self, publication_id, days=30):
        query = """
        select anonymous_id,created,id,article_id,block_id,url,referrer,
            created,user_id,block_type,ip,user_agent,languages

            from analytics_event
                where
                    publication_id = %s
                    and type = 'page'
                    and created > 'now'::date - '%s days'::interval
                order by anonymous_id, created;
        """
        with Timer('sql.analytics.sessions'):
            cursor = connection.cursor()
            cursor.execute(query, [publication_id, days])
            rows = dictfetchall(cursor)

            prev = None

            sessions = []
            session = AnalyticsSession()

            for row in rows:
                id, created = row['anonymous_id'], row['created']

                if not prev:
                    session.append(row)
                else:
                    prev_id, prev_created = (prev['anonymous_id'],
                                             prev['created'])

                    if prev_id != id:

                        if session:
                            sessions.append(session)
                            session = AnalyticsSession(rows=[row])

                    else:
                        delta = (created - prev_created).seconds

                        if delta > TRACKING_SESSION_LENGTH:
                            sessions.append(session)
                            session = AnalyticsSession(rows=[row])
                        else:
                            session.append(row)

                prev = row

            if session:
                sessions.append(session)

        return sessions

    def get_sessions_reaching_path(self, publication_id, path, days=30):
        sessions = self.get_sessions(publication_id, days=days)
        return filter(partial(has_session_reached_path, path), sessions)

    def get_per_day_session_reaching_path_grouped_range(self, sessions,
                                                        start, end):

        sessions_by_date = dict(groupby(sessions, key=lambda x: x.date_key()))
        dates = get_date_range(start, end)
        dates_items = map(lambda x: (x.strftime('%Y-%m-%d'), [],), dates)
        dates_dict = dict(dates_items)
        return merge(dates_dict, sessions_by_date)

    def get_per_day_session_reaching_path(self, sessions, days=30):
        end = datetime.utcnow()
        start = end - timedelta(days=days - 1)
        return self.get_per_day_session_reaching_path_grouped_range(sessions,
                                                                    start, end)

    def get_per_day_session_reaching_path_counts(self, sessions, days=30):
        by_date = self.get_per_day_session_reaching_path(sessions, days=days)

        for date, sessions in by_date.items():
            yield (date, len(list(sessions)),)

    def get_drop_off_report(self, publication, days=30, sessions=None):
        if not sessions:
            sessions = self.get_sessions(publication.id, days)

        paths = publication.get_publication_paths()

        for path in paths:
            s = filter(partial(has_session_reached_path, path), sessions)
            yield (path, len(s),)

    def get_unique_visitors_per_article(self, publication_id, days=30):
        query = """
        select article_id, count(distinct(anonymous_id))
            from analytics_event
                where
                    publication_id = %s
                    and type = 'page'
                    and created > 'now'::date - '%s days'::interval
                group by article_id
                order by article_id;
        """
        with Timer('sql.analytics.unique-visitors-articles'):
            cursor = connection.cursor()
            cursor.execute(query, [publication_id, days])
            rows = cursor.fetchall()

        return rows

    def get_server_unique_visitors(self, publication, days=30):
        query = """
        with distinct_entries as (
            select distinct on (anonymous_id) anonymous_id
            from analytics_event
                where
                    publication_id = %s
                    and type = 'server_pageview'
                    and created > 'now'::date - '%s days'::interval
        )
        select count(*) from distinct_entries;
        """
        with Timer('sql.analytics.server-unique-visitors'):
            cursor = connection.cursor()
            cursor.execute(query, [publication.id, days])
            rows = cursor.fetchone()
            if rows:
                rows = rows[0]

        return rows

    def get_pageviews(self, publication, days=30):
        query = """
        select count(*) from analytics_event
        where
            publication_id = %s
            and type = 'page'
            and created > 'now'::date - '%s days'::interval
        """
        with Timer('sql.analytics.pageviews'):
            cursor = connection.cursor()
            cursor.execute(query, [publication.id, days])
            rows = cursor.fetchone()
            if rows:
                rows = rows[0]

        return rows

    def get_server_pageviews(self, publication, days=30):
        query = """
        select count(*) from analytics_event
        where
            publication_id = %s
            and type = 'server_pageview'
            and created > 'now'::date - '%s days'::interval
        """
        with Timer('sql.analytics.server-pageviews'):
            cursor = connection.cursor()
            cursor.execute(query, [publication.id, days])
            rows = cursor.fetchone()
            if rows:
                rows = rows[0]

        return rows

    def article_engaged_time(self, article_id, days=30):
        now = datetime.utcnow()
        then = now - timedelta(days=days)

        qs = self.filter(created__gte=then, created__lte=now,
                         type='engaged_article', article_id=article_id)
        return qs.aggregate(models.Sum('seconds'))['seconds__sum']

    def get_percent_read(self, publication, days=30):
        article_ids = [a.pk for a in publication.articles().all()]

        if not article_ids:
            return

        query = """
        select article_id,avg(percent_read) from analytics_event
        where
            article_id in %s
            and type = 'read_article'
            and created > 'now'::date - '%s days'::interval
        group by article_id
        """

        with Timer('sql.analytics.percent-read'):
            cursor = connection.cursor()
            cursor.execute(query, [tuple(article_ids), days])
            rows = cursor.fetchall()

        return dict([(pk, {'value': int(avg)},) for pk, avg in rows])

    def get_per_article_analytics_for_users(self, publication_id, user_ids,
                                            days=30):

        if not user_ids:
            return []

        query = """
        with articles as (
            select id from projects_article where publication_id = %s
        ),

        relevant_events as (
            select user_id, article_id, type, seconds, percent_read

            from analytics_event
                where
                    article_id in (select * from articles)
                    and type in ('read_article', 'engaged_article')
                    and user_id in %s
                    and created > 'now'::date - '%s days'::interval
        )

        select relevant_events.user_id, id,
            sum(relevant_events.seconds), max(relevant_events.percent_read)

            from articles left outer join relevant_events on
                relevant_events.article_id = articles.id

            group by relevant_events.user_id, id
            order by id

        """
        with Timer('sql.per-article-reader-data'):
            cursor = connection.cursor()
            cursor.execute(query, [publication_id, tuple(user_ids), days])
            rows = cursor.fetchall()

            results = []

            for user_id, values in groupby(rows, key=lambda x: x[0]):
                articles = []

                for event_user_id, article_id, secs, percent in values:
                    articles.append({
                        'id': article_id,
                        'engaged_time': secs,
                        'percent_read': percent if percent <= 100 else 100
                    })

                results.append({
                    'user_id': user_id,
                    'articles': articles
                })

        return results

    def get_publication_readers(self, publication_id, days=30):
        query = """
        select anonymous_id,sum(seconds),max(percent_read) from analytics_event
          where
            anonymous_id is not null
              and publication_id = %s
              and created > 'now'::date - '%s days'::interval
              and type in ('engaged_publication', 'read_publication')
            group by anonymous_id;
        """
        with Timer('sql.publication-readers'):
            sessions = self.get_sessions(publication_id, days=days)
            sessions_by_user = {}

            for k, grouper in groupby(sessions, lambda x: x.user):
                sessions_by_user[k] = list(grouper)

            users = []

            cursor = connection.cursor()
            cursor.execute(query, [publication_id, days])
            rows = cursor.fetchall()

            for row in rows:
                user = {}
                user['anonymous_id'] = row[0]
                user['reader_id'] = row[0].replace('-', '')
                user['total_seconds'] = row[1]
                user['percent_read'] = row[2]
                user['sessions'] = sessions_by_user.get(row[0], None)

                users.append(user)

        return users

    def global_average_engaged_time_per_publication(self):
        query = """
        with per_pub_averages as (
            select publication_id,sum(seconds) as seconds from analytics_event
                where type = 'engaged_publication'
                group by publication_id
        )
        select avg(seconds) from per_pub_averages
        """

        with Timer('sql.global-average-engaged-time-per-publication'):
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchone()

            if rows:
                rows = rows[0]

        return rows

    def global_average_engaged_time_per_article(self):
        query = """
        with per_article_averages as (
            select article_id,sum(seconds) as seconds from analytics_event
                where type = 'engaged_article'
                group by article_id
        )
        select avg(seconds) from per_article_averages
        """

        with Timer('sql.global-average-engaged-time-per-article'):
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchone()

            if rows:
                rows = rows[0]

        return rows

    def global_average_engaged_time_per_publication_per_user(self):
        query = """
        with per_pub_averages as (
            select publication_id,anonymous_id,sum(seconds) as seconds
                from analytics_event
            where type = 'engaged_publication'
            group by publication_id,anonymous_id
        )
        select avg(seconds) from per_pub_averages
        """

        with Timer('sql.global-average-engaged-time-per-publication-per-user'):
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchone()

            if rows:
                rows = rows[0]

        return rows

    def global_average_engaged_time_per_article_per_user(self):
        query = """
        with per_article_averages as (
            select article_id,anonymous_id,sum(seconds) as seconds
                from analytics_event
            where type = 'engaged_article'
            group by article_id,anonymous_id
        )
        select avg(seconds) from per_article_averages
        """

        with Timer('sql.global-average-engaged-time-per-article-per-user'):
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchone()

            if rows:
                rows = rows[0]

        return rows

    def get_num_active_users(self):
        query = """
        select count(distinct user_id) from analytics_event
            where type = 'server_pageview'
                    and user_id is not null
                    and created > 'now'::date - '30 days'::interval;
        """
        with Timer('sql.analytics.num-active-users'):
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchone()
            if rows:
                rows = rows[0]

        return rows

    def get_num_inactive_users(self):
        active_users = self.get_num_active_users()
        all_users = get_user_model().objects.all().count()

        return all_users - active_users

    def weekly_average_logins_per_user(self):
        query = """
        with filled_dates as (
            select day, 0 as blank_count
            from generate_series(
                date_trunc('week', 'now'::date) - '6 weeks'::interval,
                current_date::date,
                '7 days') as day
        ),
        authenticated_server_pageviews as (
            select * from analytics_event
                where type = 'server_pageview'
                    and user_id is not null
        ),
        weekly_counts as (
            select date_trunc('week', created) as week, user_id,
                        count(*) as count
                from authenticated_server_pageviews
            group by user_id, date_trunc('week', created)
            order by week, user_id
        ),
        avg_weekly_counts as (
            select week,avg(count) as count from weekly_counts
                group by week
        )

        select filled_dates.day,
            coalesce(avg_weekly_counts.count, filled_dates.blank_count)
                as per_user_weekly_average
        from filled_dates
            left outer join
                avg_weekly_counts on avg_weekly_counts.week = filled_dates.day
        order by filled_dates.day;
        """

        with Timer('sql.weekly-logins-per-user'):
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        return rows


class Event(models.Model):
    TYPES = (
        ('page', 'Page',),
        ('engaged_publication', 'Engaged publication',),
        ('engaged_article', 'Engaged article',),
        ('engaged_block', 'Engaged block',),
        ('read_publication', 'Read publication',),
        ('read_article', 'Read article',),
        ('server_pageview', 'Server pageview',),
        ('action', 'Action',),
    )
    created = models.DateTimeField()
    type = models.CharField(max_length=255, choices=TYPES, db_index=True)

    user_id = models.IntegerField(null=True, blank=True)
    anonymous_id = models.CharField(max_length=255, blank=True)

    publication_id = models.IntegerField(null=True, blank=True, db_index=True)
    article_id = models.IntegerField(null=True, blank=True)
    block_id = models.IntegerField(null=True, blank=True)
    block_type = models.CharField(max_length=10, default='', blank=True)

    seconds = models.IntegerField(null=True, blank=True)
    percent_read = models.IntegerField(null=True, blank=True)

    # http://stackoverflow.com/questions/417142/what-is-the-maximum-length-of-a
    # -url-in-different-browsers
    url = models.CharField(max_length=2000, blank=True)
    referrer = models.CharField(max_length=2000, blank=True)
    social_referrer = models.CharField(max_length=255, blank=True)

    ip = models.BigIntegerField()
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    device = models.CharField(max_length=20, blank=True, null=True)
    languages = models.CharField(max_length=255, blank=True, null=True)

    continent = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)

    # actions
    action_type = models.CharField(max_length=100, blank=True, null=True)
    action_name = models.CharField(max_length=255, blank=True, null=True)
    action_value = models.CharField(max_length=255, blank=True, null=True)

    objects = EventManager()

    @property
    def is_anonymous(self):
        return self.user_id is None
