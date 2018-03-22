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
