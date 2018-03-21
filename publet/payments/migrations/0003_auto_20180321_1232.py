# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0002_auto_20180321_1232'),
        ('payments', '0002_purchase_publication'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='publicationcoupon',
            name='publication',
            field=models.ForeignKey(to='projects.Publication'),
        ),
        migrations.AddField(
            model_name='publicationcoupon',
            name='purchases',
            field=models.ManyToManyField(to='payments.Purchase', blank=True),
        ),
        migrations.AddField(
            model_name='groupsubscriptioncoupon',
            name='group',
            field=models.ForeignKey(to='groups.Group'),
        ),
        migrations.AddField(
            model_name='groupsubscriptioncoupon',
            name='purchases',
            field=models.ManyToManyField(to='payments.Purchase', blank=True),
        ),
    ]
