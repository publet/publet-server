# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import publet.common.models
from django.conf import settings
import uuidfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BulkUserUpload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('stripe_id', models.CharField(max_length=255, blank=True)),
                ('csv_data', models.TextField(help_text=b'first,last,email')),
                ('message', models.TextField(default=b'Hello, {first} {last}\n\nYou have been invited to collaborate on {groups} publications using publet.com.\n\nActivate your account to get started:\n\n{link}', help_text=b"This is the message that will be sent to the user asking\n    them to activate their account.  You can use Python's {} string\n    interpolation syntax to place some variables in.  You can use {first},\n    {last}, {email}, {groups} and {link}.\n    ", blank=True)),
                ('account_type', models.CharField(default=b'R', max_length=1, choices=[(b'B', b'Basic'), (b'P', b'Pro'), (b'R', b'Reader'), (b'T', b'Trial'), (b'F', b'Free')])),
                ('group_role', models.CharField(blank=True, max_length=1, choices=[(b'O', b'Owner'), (b'A', b'Admin'), (b'C', b'Contributor')])),
                ('created_via_admin', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('groups', models.ManyToManyField(help_text=b'A list of groups the user will have access to.', to='groups.Group', blank=True)),
                ('publications', models.ManyToManyField(to='projects.Publication', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Embed',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
                ('publication', models.ForeignKey(to='projects.Publication')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='Invite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=100, editable=False, blank=True)),
                ('active', models.BooleanField(default=False)),
                ('user_type', models.CharField(default=b'B', max_length=1, choices=[(b'B', b'Basic'), (b'P', b'Pro'), (b'R', b'Reader'), (b'T', b'Trial'), (b'F', b'Free')])),
                ('user_role', models.CharField(default=b'C', max_length=1, choices=[(b'O', b'Owner'), (b'A', b'Admin'), (b'C', b'Contributor')])),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('groups', models.ManyToManyField(to='groups.Group', blank=True)),
                ('publications', models.ManyToManyField(to='projects.Publication', blank=True)),
                ('user', models.ForeignKey(blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Signup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('first_name_and_last_name', models.CharField(max_length=255)),
                ('organization', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=255)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='Simulation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('number_of_simulations', models.IntegerField(default=10)),
                ('publications', models.ManyToManyField(to='projects.Publication')),
            ],
        ),
        migrations.CreateModel(
            name='UserAccountRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first', models.CharField(max_length=255)),
                ('last', models.CharField(max_length=255)),
                ('email', models.EmailField(unique=True, max_length=255)),
                ('notified', models.BooleanField(default=False)),
                ('uuid', uuidfield.fields.UUIDField(max_length=32, unique=True, null=True, editable=False, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('fulfilled', models.DateTimeField(null=True, blank=True)),
                ('upload', models.ForeignKey(to='utils.BulkUserUpload', null=True)),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Welcome',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('account_type', models.CharField(default=b'R', max_length=1, choices=[(b'B', b'Basic'), (b'P', b'Pro'), (b'R', b'Reader'), (b'T', b'Trial'), (b'F', b'Free')])),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('publications', models.ManyToManyField(to='projects.Publication')),
            ],
        ),
    ]
