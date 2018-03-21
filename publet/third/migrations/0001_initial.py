# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import publet.common.models
import uuidfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BufferConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('access_token', models.CharField(max_length=255)),
                ('plan', models.CharField(max_length=255, null=True, blank=True)),
                ('timezone', models.CharField(max_length=255, null=True, blank=True)),
                ('buffer_user_id', models.CharField(max_length=255, null=True, blank=True)),
                ('imported', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='BufferProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('profile_id', models.CharField(max_length=100)),
                ('service', models.CharField(max_length=255)),
                ('service_username', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='Integration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', uuidfield.fields.UUIDField(null=True, editable=False, max_length=32, blank=True, unique=True, db_index=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
    ]
