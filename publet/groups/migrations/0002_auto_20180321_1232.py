# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupmember',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='grouphub',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='grouphub',
            name='group',
            field=models.ForeignKey(to='groups.Group'),
        ),
        migrations.AddField(
            model_name='grouphub',
            name='publications',
            field=models.ManyToManyField(to='projects.Publication'),
        ),
        migrations.AlterUniqueTogether(
            name='groupmember',
            unique_together=set([('user', 'group')]),
        ),
    ]
