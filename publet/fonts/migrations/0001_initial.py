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
            name='Font',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('url', models.CharField(max_length=255, null=True, blank=True)),
                ('family', models.CharField(max_length=255, blank=True)),
                ('color', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='FontFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('file', publet.common.fields.FilePickerField(max_length=255)),
                ('filename', models.CharField(max_length=255)),
                ('style', models.CharField(default=b'normal', max_length=11, choices=[(b'normal', b'normal'), (b'italic', b'italic'), (b'bold', b'bold'), (b'italic-bold', b'italic-bold')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
    ]
