# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='publication',
            field=models.ForeignKey(blank=True, to='projects.Publication', null=True),
        ),
    ]
