# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import re
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='PubletUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('username', models.CharField(unique=True, max_length=30, validators=[django.core.validators.RegexValidator(re.compile(b'^[\\w.@+-]+$'), b'Enter a valid username.', b'invalid')])),
                ('first_name', models.CharField(max_length=30, blank=True)),
                ('last_name', models.CharField(max_length=30, blank=True)),
                ('email', models.EmailField(unique=True, max_length=254)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('date_joined', models.DateTimeField(default=datetime.datetime.utcnow)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_superuser', models.BooleanField(default=False)),
                ('job_title', models.CharField(max_length=255, null=True, blank=True)),
                ('twitter', models.CharField(max_length=100, null=True, blank=True)),
                ('facebook', models.CharField(max_length=255, null=True, blank=True)),
                ('linkedin', models.CharField(max_length=255, null=True, blank=True)),
                ('googleplus', models.CharField(max_length=255, null=True, blank=True)),
                ('account_type', models.CharField(default=b'R', max_length=1, choices=[(b'B', b'Basic'), (b'P', b'Pro'), (b'R', b'Reader'), (b'T', b'Trial'), (b'F', b'Free')])),
                ('stripe_id', models.CharField(max_length=100, null=True, blank=True)),
                ('groups', models.ManyToManyField(related_query_name=b'publetuser', related_name='publetuser_set', to='auth.Group', blank=True)),
                ('user_permissions', models.ManyToManyField(related_query_name=b'publetuser', related_name='publetuser_set', to='auth.Permission', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PubletApiKey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(default=b'', max_length=128, db_index=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(related_name='publet_api_key', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
