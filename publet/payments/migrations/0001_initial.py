# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupSubscriptionCoupon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=False)),
                ('code', models.CharField(unique=True, max_length=20)),
                ('expires', models.DateTimeField(null=True, blank=True)),
                ('new_price', models.IntegerField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PublicationCoupon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=False)),
                ('code', models.CharField(unique=True, max_length=20)),
                ('expires', models.DateTimeField(null=True, blank=True)),
                ('new_price', models.IntegerField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('purchase_type', models.CharField(max_length=50, choices=[(b'publication', b'Publication'), (b'subscription', b'Subscription')])),
                ('stripe_id', models.CharField(default=b'', max_length=100)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(blank=True, to='groups.Group', null=True)),
            ],
        ),
    ]
