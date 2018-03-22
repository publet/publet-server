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
from datetime import datetime

from annoying.functions import get_object_or_None
from django_rq import job

from models import Integration, BufferProfile
from buffer import get_buffer_api, submit_to_buffer


@job
def import_buffer_profiles(integration_pk):
    integration = get_object_or_None(Integration, pk=integration_pk)

    if not integration:
        raise Exception('Integration not found')

    conf = integration.bufferconfig

    BufferProfile.objects.filter(token__integration=integration).delete()

    api = get_buffer_api(integration)

    profiles = api.get(url='profiles.json').json()
    BufferProfile.bulk_create_profiles(conf, profiles)

    conf.imported = datetime.utcnow()
    conf.save()


@job
def import_buffer_user_data(integration_pk):
    integration = get_object_or_None(Integration, pk=integration_pk)

    if not integration:
        raise Exception('Integration not found')

    conf = integration.bufferconfig
    api = get_buffer_api(integration)

    user = api.get(url='user.json').json()

    conf.plan = user['plan']
    conf.timezone = user['timezone']
    conf.buffer_user_id = user['id']

    conf.save()


@job
def submit_to_integration(integration_pk, block_type, block_id):
    from publet.projects.models import get_block_type
    integration = get_object_or_None(Integration, pk=integration_pk)

    if not integration:
        raise Exception('Integration not found')

    Class = get_block_type(block_type)
    block = get_object_or_None(Class, pk=block_id)

    if not block:
        raise Exception('Block not found')

    if block.type == 'text':
        message = block.as_plain_text()
        image_url = None
    elif block.type == 'gallery':
        message = None
        photos = block.ordered_photos()

        if not photos:
            raise Exception('No photos found')

        image_url = photos[0].get_image_url()
    else:
        raise Exception('Unknown block type')

    submit_to_buffer(integration, message, image_url)
