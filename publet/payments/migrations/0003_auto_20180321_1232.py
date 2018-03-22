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
