import logging
import json
import redis
from raven.contrib.django.raven_compat.models import client
from django.core.management.base import BaseCommand
from publet.analytics.tasks import process_analytics_hit
from publet.utils.metrics import Gauge


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        r = redis.StrictRedis(db=0)

        logger.info('Listening...')

        while True:
            value = r.brpoplpush('track:queue', 'track:processing', timeout=0)
            logger.info('Received value')

            try:
                data = json.loads(value)
                process_analytics_hit(data, value)
            except Exception:
                client.captureException()
                logger.error('Failed to parse data')
                r.rpush('track:failed', value)
                r.lrem('track:processing', 0, value)
                continue

            logger.info('Success')

            count = r.llen('track:queue')
            Gauge('track.events.queue-size').report(count)
