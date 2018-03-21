# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import publet.common.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.CharField(unique=True, max_length=255)),
                ('is_active', models.BooleanField(default=False)),
                ('requires_staff', models.BooleanField(default=False)),
                ('requires_superuser', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
    ]
