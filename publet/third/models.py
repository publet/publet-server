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
from functools import partial

from django.db import models
from uuidfield import UUIDField

from publet.common.models import BaseModel
from publet.groups.models import Group


class Integration(BaseModel):
    name = models.CharField(max_length=255)
    group = models.ForeignKey(Group)
    slug = UUIDField(auto=True, null=True, db_index=True)

    def __unicode__(self):
        return '<Integration: {}>'.format(self.name)


class BufferConfig(BaseModel):
    integration = models.OneToOneField(Integration)

    access_token = models.CharField(max_length=255)
    plan = models.CharField(max_length=255, null=True, blank=True)
    timezone = models.CharField(max_length=255, null=True, blank=True)
    buffer_user_id = models.CharField(max_length=255, null=True, blank=True)

    imported = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return '<BufferConfig: {}>'.format(self.access_token)


class BufferProfile(BaseModel):
    token = models.ForeignKey(BufferConfig)

    profile_id = models.CharField(max_length=100)
    service = models.CharField(max_length=255)  # twitter, facebook, etc
    service_username = models.CharField(max_length=255)

    def __unicode__(self):
        return '<BufferProfile: {}>'.format(self.profile_id)

    @classmethod
    def new_from_json(cls, token_obj, profile):
        return cls(token=token_obj, profile_id=profile['id'],
                   service=profile['service'],
                   service_username=profile['service_username'])

    @classmethod
    def bulk_create_profiles(cls, token_obj, profiles):
        f = partial(cls.new_from_json, token_obj)
        objs = map(f, profiles)
        return cls.objects.bulk_create(objs)
