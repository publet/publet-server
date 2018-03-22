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
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField()),
                ('type', models.CharField(db_index=True, max_length=255, choices=[(b'page', b'Page'), (b'engaged_publication', b'Engaged publication'), (b'engaged_article', b'Engaged article'), (b'engaged_block', b'Engaged block'), (b'read_publication', b'Read publication'), (b'read_article', b'Read article'), (b'server_pageview', b'Server pageview'), (b'action', b'Action')])),
                ('user_id', models.IntegerField(null=True, blank=True)),
                ('anonymous_id', models.CharField(max_length=255, blank=True)),
                ('publication_id', models.IntegerField(db_index=True, null=True, blank=True)),
                ('article_id', models.IntegerField(null=True, blank=True)),
                ('block_id', models.IntegerField(null=True, blank=True)),
                ('block_type', models.CharField(default=b'', max_length=10, blank=True)),
                ('seconds', models.IntegerField(null=True, blank=True)),
                ('percent_read', models.IntegerField(null=True, blank=True)),
                ('url', models.CharField(max_length=2000, blank=True)),
                ('referrer', models.CharField(max_length=2000, blank=True)),
                ('social_referrer', models.CharField(max_length=255, blank=True)),
                ('ip', models.BigIntegerField()),
                ('user_agent', models.CharField(max_length=500, null=True, blank=True)),
                ('device', models.CharField(max_length=20, null=True, blank=True)),
                ('languages', models.CharField(max_length=255, null=True, blank=True)),
                ('continent', models.CharField(max_length=255, null=True, blank=True)),
                ('country', models.CharField(max_length=255, null=True, blank=True)),
                ('region', models.CharField(max_length=255, null=True, blank=True)),
                ('city', models.CharField(max_length=255, null=True, blank=True)),
                ('action_type', models.CharField(max_length=100, null=True, blank=True)),
                ('action_name', models.CharField(max_length=255, null=True, blank=True)),
                ('action_value', models.CharField(max_length=255, null=True, blank=True)),
            ],
        ),
    ]
