import logging
import redis
from django_rq import job
from core import parse_raw_data, save_events


logger = logging.getLogger(__name__)


r = redis.StrictRedis(db=0)


@job
def process_analytics_hit(data, value):
    events = parse_raw_data(data)

    try:

        if not events:
            logger.info('No events to save')
            return

        save_events(events)

    except Exception, e:
        logger.error('Failed to save events', e)
        r.rpush('track:failed', value)

    finally:
        r.lrem('track:processing', 0, value)
