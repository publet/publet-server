from datetime import datetime, timedelta

from django.test import TestCase

from publet.analytics.models import Event, AnalyticsSession, get_date_range


class EngagedTimeTest(TestCase):

    def setUp(self):
        pass

    def test_daily_average_publication_engaged_time(self):
        now = datetime.now() - timedelta(days=2)
        Event.objects.create(created=now, publication_id=1,
                             type='engaged_publication', user_id=1, ip=1,
                             seconds=3)

        # Simplest case, one item
        res = Event.objects.daily_average_publication_engaged_time(1)
        self.assertEquals(len(res), 31)
        day_in_question = res[-3]
        self.assertEquals(day_in_question[0].date(), now.date())
        self.assertEquals(int(day_in_question[1]), 3)

        # Add second item on same day, check average
        Event.objects.create(created=now, publication_id=1,
                             type='engaged_publication', user_id=2, ip=1,
                             seconds=7)
        res = Event.objects.daily_average_publication_engaged_time(1)
        self.assertEquals(len(res), 31)
        day_in_question = res[-3]
        self.assertEquals(day_in_question[0].date(), now.date())
        self.assertEquals(int(day_in_question[1]), 5)

        # Add item on different day
        now2 = datetime.now() - timedelta(days=5)
        Event.objects.create(created=now2, publication_id=1,
                             type='engaged_publication', user_id=2, ip=1,
                             seconds=2)
        res = Event.objects.daily_average_publication_engaged_time(1)
        self.assertEquals(len(res), 31)
        day_in_question = res[-3]
        self.assertEquals(day_in_question[0].date(), now.date())
        self.assertEquals(int(day_in_question[1]), 5)
        day_in_question = res[-6]
        self.assertEquals(day_in_question[0].date(), now2.date())
        self.assertEquals(int(day_in_question[1]), 2)

        # Add an event for the same publication but different type
        Event.objects.create(created=now, publication_id=1, type='page',
                             user_id=1, ip=1, seconds=3)
        res = Event.objects.daily_average_publication_engaged_time(1)
        self.assertEquals(len(res), 31)
        day_in_question = res[-3]
        self.assertEquals(day_in_question[0].date(), now.date())
        self.assertEquals(int(day_in_question[1]), 5)

    def test_per_block_engaged_data(self):
        # Empty first
        res = Event.objects.get_per_block_engaged_data(1)
        self.assertEquals(0, len(res))

        res = Event.objects.get_per_block_engaged_data_normalized(1)
        self.assertEquals(0, len(res))

        now = datetime.now() - timedelta(days=2)

        Event.objects.create(created=now, publication_id=1,
                             type='engaged_block', user_id=1, ip=1, seconds=3,
                             block_id=1)
        Event.objects.create(created=now, publication_id=1,
                             type='engaged_block', user_id=1, ip=1, seconds=7,
                             block_id=1)

        res = Event.objects.get_per_block_engaged_data(1)

        self.assertNotEquals(len(res), 0)
        block_id, value = res[0]
        self.assertEquals(block_id, 1)
        self.assertEquals(value, 10)


class PageViewTest(TestCase):

    def test_sessions(self):
        res = Event.objects.get_sessions(1)
        self.assertEquals(0, len(res))

        now = datetime.now() - timedelta(days=2)

        # First hit, session 1
        Event.objects.create(created=now, publication_id=1, type='page',
                             user_id=1, ip=1, anonymous_id='abc')

        now = now + timedelta(minutes=10)

        # Second hit, still session 1
        Event.objects.create(created=now, publication_id=1, type='page',
                             user_id=1, ip=1, anonymous_id='abc')

        now = now + timedelta(minutes=5)

        # Third hit, still session 1
        Event.objects.create(created=now, publication_id=1, type='page',
                             user_id=1, ip=1, anonymous_id='abc')

        now = now + timedelta(minutes=10)

        # Fourth hit, session 1
        Event.objects.create(created=now, publication_id=1, type='page',
                             user_id=1, ip=1, anonymous_id='abc')

        # Fifth hit, session 2
        now = now + timedelta(minutes=50)
        Event.objects.create(created=now, publication_id=1, type='page',
                             user_id=1, ip=1, anonymous_id='abc')

        # Second user, session 3
        other_user_now = now + timedelta(minutes=5)
        Event.objects.create(created=other_user_now, publication_id=1,
                             type='page', user_id=2, ip=1, anonymous_id='defg')

        res = Event.objects.get_sessions(1)
        self.assertEquals(3, len(res))

    def test_session_object(self):
        session = AnalyticsSession()
        self.assertFalse(bool(session))

        session.append(1)
        self.assertTrue(bool(session))

        rows = [
            {'anonymous_id': 'abc'},
            {'anonymous_id': 'abc'},
            {'anonymous_id': 'abc'},
        ]

        session = AnalyticsSession(rows=rows)
        self.assertEquals(3, len(session))

        for row, i in zip(session, rows):
            self.assertEquals(row, i)

        created = datetime(2015, 4, 10, 13, 30, 0)
        row = {'created': created, 'anonymous_id': 'abc'}
        session = AnalyticsSession(rows=[row])

        self.assertEquals(created, session.date())
        self.assertEquals('2015-04-10', session.date_key())

    def test_session_reaching_path(self):
        self.assertEquals(
            0, len(Event.objects.get_sessions_reaching_path(1, 'abc')))

        now = datetime.now() - timedelta(days=2)

        # First hit, session 1
        Event.objects.create(created=now, publication_id=1, type='page',
                             user_id=1, ip=1, anonymous_id='abc', url='abc')

        now = now + timedelta(minutes=10)

        # Second hit, still session 1
        Event.objects.create(created=now, publication_id=1, type='page',
                             user_id=1, ip=1, anonymous_id='abc', url='abc')

        now = now + timedelta(minutes=5)

        # Third hit, still session 1
        Event.objects.create(created=now, publication_id=1, type='page',
                             user_id=1, ip=1, anonymous_id='abc')

        now = now + timedelta(minutes=10)

        # Fourth hit, session 1
        Event.objects.create(created=now, publication_id=1, type='page',
                             user_id=1, ip=1, anonymous_id='abc')

        # Fifth hit, session 2
        now = now + timedelta(minutes=50)
        Event.objects.create(created=now, publication_id=1, type='page',
                             user_id=1, ip=1, anonymous_id='abc')

        # Second user, session 3
        other_user_now = now + timedelta(minutes=5)
        Event.objects.create(created=other_user_now, publication_id=1,
                             type='page', user_id=2, ip=1, anonymous_id='defg')

        self.assertEquals(
            1, len(Event.objects.get_sessions_reaching_path(1, 'abc')))

    def test_date_range(self):
        start = datetime(2015, 4, 10, 13, 0, 0)
        end = start + timedelta(days=29)

        dates = get_date_range(start, end)
        self.assertEquals(30, len(dates))
        self.assertEquals(start.date(), dates[0])
        self.assertEquals(end.date(), dates[-1])
        self.assertEquals(datetime(2015, 4, 11, 0, 0, 0).date(), dates[1])

    def test_per_day_session_reaching_path_count(self):
        now = datetime.utcnow()
        then = now - timedelta(days=5)
        sessions = []

        sessions.append(AnalyticsSession(rows=[
            dict(url='abc', created=then, anonymous_id='abc')
        ]))

        end = now
        start = now - timedelta(days=29)
        then_key = then.strftime('%Y-%m-%d')

        res = Event.objects.get_per_day_session_reaching_path_grouped_range(
            sessions, start, end)

        self.assertTrue(then_key in res)
        self.assertEquals(1, len(list(res[then_key])))

        res = Event.objects.get_per_day_session_reaching_path(sessions)

        self.assertTrue(then_key in res)
        self.assertEquals(1, len(list(res[then_key])))

        res = Event.objects.get_per_day_session_reaching_path_counts(sessions)

        self.assertEquals(30, len(list(res)))

        for date, session_count in res:
            if date == then_key:
                self.assertEquals(1, session_count)
            else:
                self.assertEquals(0, session_count)

    def test_unique_visitors_per_article(self):
        now = datetime.now() - timedelta(days=2)

        Event.objects.create(created=now, publication_id=1, article_id=11,
                             type='page', user_id=1, ip=1, anonymous_id='abc')

        Event.objects.create(created=now, publication_id=1, article_id=11,
                             type='page', user_id=1, ip=1, anonymous_id='abc')

        Event.objects.create(created=now, publication_id=1, article_id=22,
                             type='page', user_id=2, ip=1, anonymous_id='abc')

        Event.objects.create(created=now, publication_id=1, article_id=22,
                             type='page', user_id=2, ip=1, anonymous_id='xxx')

        res = Event.objects.get_unique_visitors_per_article(1)
        self.assertEquals(2, len(res))  # Two articles

        self.assertEquals(11, res[0][0])  # Article ID
        self.assertEquals(22, res[1][0])  # Article ID

        self.assertEquals(1, res[0][1])
        self.assertEquals(2, res[1][1])

    def test_global_pageviews_per_pub(self):
        res = Event.objects.get_global_unique_visitors_per_publication()
        self.assertEquals(0, len(res))

        now = datetime.now() - timedelta(days=2)

        Event.objects.create(created=now, publication_id=20, article_id=2,
                             type='page', user_id=2, ip=1, anonymous_id='xxx')

        res = Event.objects.get_global_unique_visitors_per_publication()
        self.assertEquals(1, len(res))
        self.assertEquals(1, res[0][1])

        Event.objects.create(created=now, publication_id=20, article_id=2,
                             type='page', user_id=2, ip=1, anonymous_id='xxx')

        Event.objects.create(created=now, publication_id=20, article_id=2,
                             type='page', user_id=2, ip=1, anonymous_id='abc')

        res = Event.objects.get_global_unique_visitors_per_publication()
        self.assertEquals(1, len(res))  # Still only one publication
        self.assertEquals(2, res[0][1])  # Two uniques in the only publication
