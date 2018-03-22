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
import publet.common.fields
import publet.common.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(unique=True, max_length=255, blank=True)),
                ('plan_id', models.CharField(default=b'', max_length=100, null=True, blank=True)),
                ('price', models.IntegerField(default=0, null=True, blank=True)),
                ('domain', models.CharField(max_length=255, null=True, blank=True)),
                ('favicon', publet.common.fields.FilePickerField(max_length=255, null=True, blank=True)),
                ('favicon_filename', models.CharField(max_length=255, null=True, blank=True)),
                ('ga_tracking_id', models.CharField(max_length=20, blank=True)),
                ('mailchimp_account_id', models.CharField(max_length=255, blank=True)),
                ('sharpspring_id', models.CharField(max_length=255, blank=True)),
                ('splyt_id', models.CharField(max_length=255, blank=True)),
                ('twitter', models.CharField(max_length=200, blank=True)),
                ('facebook', models.CharField(max_length=200, blank=True)),
                ('pinterest', models.CharField(max_length=200, blank=True)),
                ('linkedin', models.CharField(max_length=200, blank=True)),
                ('api', models.CharField(default=b'n', max_length=1, choices=[(b'n', b'No API'), (b'p', b'Public API'), (b'r', b'Private API')])),
                ('has_publish_dates', models.BooleanField(default=False)),
                ('description', models.TextField(null=True, blank=True)),
                ('logo', publet.common.fields.FilePickerField(max_length=255, null=True, blank=True)),
                ('logo_filename', models.CharField(max_length=255, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            bases=(models.Model, publet.common.models.CDNMixin),
        ),
        migrations.CreateModel(
            name='GroupHub',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(unique=True, max_length=255, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='GroupMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(default=b'C', max_length=1, choices=[(b'O', b'Owner'), (b'E', b'Editor'), (b'C', b'Contributor'), (b'R', b'Reviewer'), (b'A', b'Admin'), (b'D', b'Developer')])),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(to='groups.Group')),
            ],
        ),
    ]
