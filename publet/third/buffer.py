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
from django.conf import settings
from buffpy import AuthService


BUFFER_OAUTH_CALLBACK = getattr(settings, 'BUFFER_OAUTH_CALLBACK')
BUFFER_OAUTH_CLIENT_ID = getattr(settings, 'BUFFER_OAUTH_CLIENT_ID')
BUFFER_OAUTH_CLIENT_SECRET = getattr(settings, 'BUFFER_OAUTH_CLIENT_SECRET')


class BufferAuthService(AuthService):

    def get_authorize_url_with_state(self, state):
        return self.outh_service.get_authorize_url(
            response_type='code', state=state, redirect_uri=self.redirect_uri)


def get_buffer_api(integration):
    conf = integration.bufferconfig
    access_token = conf.access_token
    service = BufferAuthService(BUFFER_OAUTH_CLIENT_ID,
                                BUFFER_OAUTH_CLIENT_SECRET,
                                BUFFER_OAUTH_CALLBACK)
    return service.create_session(access_token)


def submit_to_buffer(integration, message, image_url=None):
    profiles = integration.bufferconfig.bufferprofile_set.all()
    profile_ids = [p.profile_id for p in profiles]

    data = {
        'profile_ids[]': profile_ids,
        'text': message
    }

    if image_url:
        data['media[photo]'] = image_url
        data['media[thumbnail]'] = image_url

    api = get_buffer_api(integration)
    r = api.post(url='updates/create.json', data=data)
    return r.status_code == 200
