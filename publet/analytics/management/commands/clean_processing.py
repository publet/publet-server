import logging
import json
import redis
from django.core.management.base import BaseCommand
from publet.analytics.tasks import process_analytics_hit


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        r = redis.StrictRedis(db=0)

        count = r.llen('track:processing')
        logger.info('{} items to process'.format(count))

        while True:
            value = r.rpop('track:processing')

            if not value:
                break

            logger.info('Received value')

            try:
                data = json.loads(value)
            except Exception, e:
                logger.error('Failed to parse data: ' + str(e))
                r.rpush('track:failed', value)
                r.lrem('track:processing', 0, value)
                continue

            process_analytics_hit(data, value)
            logger.info('Success')
