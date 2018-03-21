# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0002_auto_20180321_1232'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fonts', '0002_auto_20180321_1232'),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='videoblock',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='videoblock',
            name='flavor',
            field=models.ForeignKey(to='projects.Flavor'),
        ),
        migrations.AddField(
            model_name='videoblock',
            name='font',
            field=models.ForeignKey(blank=True, to='fonts.Font', null=True),
        ),
        migrations.AddField(
            model_name='type',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='background_color',
            field=models.ForeignKey(related_name='background', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='fonts',
            field=models.ManyToManyField(to='fonts.Font', blank=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='group',
            field=models.ForeignKey(blank=True, to='groups.Group', null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='header_color',
            field=models.ForeignKey(related_name='header', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='heading_color',
            field=models.ForeignKey(related_name='heading', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='link_color',
            field=models.ForeignKey(related_name='link', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='nav_background_color',
            field=models.ForeignKey(related_name='nav', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='nav_font_color',
            field=models.ForeignKey(related_name='nav_bg', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='toc_background_color',
            field=models.ForeignKey(related_name='toc_background', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='toc_color',
            field=models.ForeignKey(related_name='toc_font_color', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='textblock',
            name='article',
            field=models.ForeignKey(blank=True, to='projects.Article', null=True),
        ),
        migrations.AddField(
            model_name='textblock',
            name='background_color',
            field=models.ForeignKey(related_name='text_background_color', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='textblock',
            name='color',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='textblock',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='textblock',
            name='flavor',
            field=models.ForeignKey(to='projects.Flavor'),
        ),
        migrations.AddField(
            model_name='textblock',
            name='font',
            field=models.ForeignKey(blank=True, to='fonts.Font', null=True),
        ),
        migrations.AddField(
            model_name='readability',
            name='article',
            field=models.ForeignKey(blank=True, to='projects.Article', null=True),
        ),
        migrations.AddField(
            model_name='readability',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='readability',
            name='publication',
            field=models.ForeignKey(to='projects.Publication'),
        ),
        migrations.AddField(
            model_name='publicationsocialgateentry',
            name='publication',
            field=models.ForeignKey(blank=True, to='projects.Publication', null=True),
        ),
        migrations.AddField(
            model_name='publicationslug',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='publicationslug',
            name='publication',
            field=models.ForeignKey(to='projects.Publication'),
        ),
        migrations.AddField(
            model_name='publication',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='publication',
            name='group',
            field=models.ForeignKey(to='groups.Group'),
        ),
        migrations.AddField(
            model_name='publication',
            name='new_theme',
            field=models.ForeignKey(blank=True, to='projects.NewTheme', null=True),
        ),
        migrations.AddField(
            model_name='publication',
            name='theme',
            field=models.ForeignKey(blank=True, to='projects.Theme', null=True),
        ),
        migrations.AddField(
            model_name='publication',
            name='type',
            field=models.ForeignKey(blank=True, to='projects.Type', null=True),
        ),
        migrations.AddField(
            model_name='presetitem',
            name='preset',
            field=models.ForeignKey(to='projects.Preset'),
        ),
        migrations.AddField(
            model_name='preset',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='preset',
            name='publication_type',
            field=models.ForeignKey(blank=True, to='projects.Type', null=True),
        ),
        migrations.AddField(
            model_name='photoblock',
            name='article',
            field=models.ForeignKey(blank=True, to='projects.Article', null=True),
        ),
        migrations.AddField(
            model_name='photoblock',
            name='color',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='photoblock',
            name='cover_color_subtitle',
            field=models.ForeignKey(related_name='cover_colors_subtitle', blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='photoblock',
            name='cover_color_title',
            field=models.ForeignKey(related_name='cover_colors_title', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='photoblock',
            name='cover_font_subtitle',
            field=models.ForeignKey(related_name='cover_font_subtitle', blank=True, to='fonts.Font', null=True),
        ),
        migrations.AddField(
            model_name='photoblock',
            name='cover_font_title',
            field=models.ForeignKey(related_name='cover_font_title', blank=True, to='fonts.Font', null=True),
        ),
        migrations.AddField(
            model_name='photoblock',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='photoblock',
            name='flavor',
            field=models.ForeignKey(to='projects.Flavor'),
        ),
        migrations.AddField(
            model_name='photoblock',
            name='font',
            field=models.ForeignKey(blank=True, to='fonts.Font', null=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='block',
            field=models.ForeignKey(to='projects.PhotoBlock'),
        ),
        migrations.AddField(
            model_name='photo',
            name='description_color',
            field=models.ForeignKey(related_name='colors', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='description_font',
            field=models.ForeignKey(blank=True, to='fonts.Font', null=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='heading_color',
            field=models.ForeignKey(related_name='heading_colors', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='heading_font',
            field=models.ForeignKey(related_name='heading_font', blank=True, to='fonts.Font', null=True),
        ),
        migrations.AddField(
            model_name='pdfupload',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='pdfupload',
            name='publication',
            field=models.ForeignKey(to='projects.Publication'),
        ),
        migrations.AddField(
            model_name='newtheme',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='newtheme',
            name='group',
            field=models.ForeignKey(to='groups.Group'),
        ),
        migrations.AddField(
            model_name='newarticle',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='newarticle',
            name='publication',
            field=models.ForeignKey(to='projects.Publication'),
        ),
        migrations.AddField(
            model_name='gatesubmission',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='gatesubmission',
            name='publication',
            field=models.ForeignKey(to='projects.Publication'),
        ),
        migrations.AddField(
            model_name='flavor',
            name='background_color',
            field=models.ForeignKey(related_name='background_color', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='flavor',
            name='color',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='flavor',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='flavor',
            name='font',
            field=models.ForeignKey(blank=True, to='fonts.Font', null=True),
        ),
        migrations.AddField(
            model_name='flavor',
            name='theme',
            field=models.ForeignKey(to='projects.Theme'),
        ),
        migrations.AddField(
            model_name='event',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='parent_article',
            field=models.ForeignKey(blank=True, to='projects.Article', null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='parent_publication',
            field=models.ForeignKey(blank=True, to='projects.Publication', null=True),
        ),
        migrations.AddField(
            model_name='color',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='color',
            name='theme',
            field=models.ForeignKey(to='projects.Theme', null=True),
        ),
        migrations.AddField(
            model_name='audioblock',
            name='article',
            field=models.ForeignKey(blank=True, to='projects.Article', null=True),
        ),
        migrations.AddField(
            model_name='audioblock',
            name='color',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True),
        ),
        migrations.AddField(
            model_name='audioblock',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='audioblock',
            name='flavor',
            field=models.ForeignKey(to='projects.Flavor'),
        ),
        migrations.AddField(
            model_name='audioblock',
            name='font',
            field=models.ForeignKey(blank=True, to='fonts.Font', null=True),
        ),
        migrations.AddField(
            model_name='asset',
            name='block',
            field=models.ForeignKey(to='projects.TextBlock'),
        ),
        migrations.AddField(
            model_name='asset',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='article',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='article',
            name='parent',
            field=models.ForeignKey(blank=True, to='projects.Article', null=True),
        ),
        migrations.AddField(
            model_name='article',
            name='preset',
            field=models.ForeignKey(blank=True, to='projects.Preset', null=True),
        ),
        migrations.AddField(
            model_name='article',
            name='publication',
            field=models.ForeignKey(to='projects.Publication', blank=True),
        ),
        migrations.AddField(
            model_name='article',
            name='theme',
            field=models.ForeignKey(blank=True, to='projects.Theme', null=True),
        ),
    ]
