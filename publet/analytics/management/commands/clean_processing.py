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
