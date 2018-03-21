# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0002_auto_20180321_1232'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('third', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='integration',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='integration',
            name='group',
            field=models.ForeignKey(to='groups.Group'),
        ),
        migrations.AddField(
            model_name='bufferprofile',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='bufferprofile',
            name='token',
            field=models.ForeignKey(to='third.BufferConfig'),
        ),
        migrations.AddField(
            model_name='bufferconfig',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='bufferconfig',
            name='integration',
            field=models.OneToOneField(to='third.Integration'),
        ),
    ]
