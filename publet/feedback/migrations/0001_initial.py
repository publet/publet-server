# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import publet.common.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('type', models.IntegerField(choices=[(1, b'New integration'), (2, b'I wish')])),
                ('message', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
    ]
