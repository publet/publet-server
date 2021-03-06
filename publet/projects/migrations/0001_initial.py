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
import django_pgjson.fields
import publet.common.fields
import publet.projects.models
import django.db.models.deletion
import publet.common.models
import uuidfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(unique=True, max_length=255, blank=True)),
                ('order', models.IntegerField(default=-1)),
                ('uuid', uuidfield.fields.UUIDField(max_length=32, unique=True, null=True, editable=False, blank=True)),
                ('domain', models.CharField(max_length=255, null=True, blank=True)),
                ('hosted_password', models.CharField(max_length=255, null=True, blank=True)),
                ('is_toc', models.BooleanField(default=False)),
                ('gate_copy', models.TextField(null=True, blank=True)),
                ('is_draft', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin, publet.projects.models.BlockTypeMixin),
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('filename', models.CharField(max_length=255, blank=True)),
                ('label', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin, publet.projects.models.DirtyMixin, publet.common.models.CDNMixin),
        ),
        migrations.CreateModel(
            name='AudioBlock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('size', models.PositiveIntegerField(null=True, blank=True)),
                ('line_height', models.CharField(max_length=10, blank=True)),
                ('meta', models.CharField(max_length=1000, blank=True)),
                ('custom_css_classes', models.CharField(max_length=255, blank=True)),
                ('alignment', models.CharField(blank=True, max_length=1, choices=[(b'0', b'Column'), (b'1', b'Full'), (b'2', b'Breaking'), (b'3', b'Breaking left'), (b'4', b'Breaking right'), (b'5', b'Margin left'), (b'6', b'Margin right'), (b'7', b'Column left'), (b'8', b'Column right')])),
                ('text_alignment', models.CharField(blank=True, max_length=1, choices=[(b'l', b'left'), (b'r', b'right'), (b'c', b'center')])),
                ('order', models.IntegerField(default=-1)),
                ('is_locked', models.BooleanField(default=False)),
                ('shareable', models.BooleanField(default=False)),
                ('audio_url', models.CharField(max_length=255)),
                ('label', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin, publet.projects.models.DirtyMixin),
        ),
        migrations.CreateModel(
            name='Color',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('hex', models.CharField(max_length=10)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('type', models.PositiveIntegerField(choices=[(1, b'Article added'), (2, b'Article removed'), (3, b'Text block added'), (4, b'Photo block added'), (5, b'Audio block added'), (6, b'Video block added'), (7, b'Text block removed'), (8, b'Photo block removed'), (9, b'Audio block removed'), (10, b'Video block removed')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='Flavor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('size', models.PositiveIntegerField(null=True, blank=True)),
                ('line_height', models.CharField(max_length=10, blank=True)),
                ('meta', models.CharField(max_length=1000, blank=True)),
                ('custom_css_classes', models.CharField(max_length=255, blank=True)),
                ('alignment', models.CharField(blank=True, max_length=1, choices=[(b'0', b'Column'), (b'1', b'Full'), (b'2', b'Breaking'), (b'3', b'Breaking left'), (b'4', b'Breaking right'), (b'5', b'Margin left'), (b'6', b'Margin right'), (b'7', b'Column left'), (b'8', b'Column right')])),
                ('text_alignment', models.CharField(blank=True, max_length=1, choices=[(b'l', b'left'), (b'r', b'right'), (b'c', b'center')])),
                ('name', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=5, choices=[(b'text', b'Text'), (b'photo', b'Photo'), (b'audio', b'Audio'), (b'video', b'Video')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='GateSubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('data', django_pgjson.fields.JsonField()),
                ('anonymous_id', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='NewArticle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('order', models.IntegerField(default=0)),
                ('data', django_pgjson.fields.JsonField()),
                ('id_counter', models.IntegerField(default=0)),
                ('sha', models.CharField(max_length=40, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='NewTheme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('data', django_pgjson.fields.JsonField(blank=True)),
                ('id_counter', models.IntegerField(default=0)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='PDFUpload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('url', publet.common.fields.FilePickerField(unique=True, max_length=255)),
                ('filename', models.CharField(max_length=255)),
                ('processed', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(default=-1)),
                ('image', publet.common.fields.FilePickerField(max_length=255)),
                ('link', models.CharField(max_length=255, blank=True)),
                ('heading', models.CharField(max_length=255, blank=True)),
                ('description', models.CharField(max_length=255, blank=True)),
                ('heading_size', models.PositiveIntegerField(default=18)),
                ('heading_text_alignment', models.CharField(default=b'l', max_length=1, choices=[(b'l', b'left'), (b'r', b'right'), (b'c', b'center')])),
                ('description_size', models.PositiveIntegerField(default=18)),
                ('description_text_alignment', models.CharField(default=b'l', max_length=1, choices=[(b'l', b'left'), (b'r', b'right'), (b'c', b'center')])),
                ('has_shadow', models.BooleanField(default=False)),
                ('crop_marks', models.CharField(max_length=200, blank=True)),
                ('width', models.PositiveIntegerField(null=True, blank=True)),
                ('height', models.PositiveIntegerField(null=True, blank=True)),
                ('size', models.CharField(default=b'l', max_length=1, choices=[(b's', b'Small'), (b'm', b'Medium'), (b'l', b'Large')])),
                ('trigger_gate', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            bases=(models.Model, publet.projects.models.DirtyMixin, publet.projects.models.CropMixin, publet.common.models.CDNMixin),
        ),
        migrations.CreateModel(
            name='PhotoBlock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('size', models.PositiveIntegerField(null=True, blank=True)),
                ('line_height', models.CharField(max_length=10, blank=True)),
                ('meta', models.CharField(max_length=1000, blank=True)),
                ('custom_css_classes', models.CharField(max_length=255, blank=True)),
                ('alignment', models.CharField(blank=True, max_length=1, choices=[(b'0', b'Column'), (b'1', b'Full'), (b'2', b'Breaking'), (b'3', b'Breaking left'), (b'4', b'Breaking right'), (b'5', b'Margin left'), (b'6', b'Margin right'), (b'7', b'Column left'), (b'8', b'Column right')])),
                ('text_alignment', models.CharField(blank=True, max_length=1, choices=[(b'l', b'left'), (b'r', b'right'), (b'c', b'center')])),
                ('order', models.IntegerField(default=-1)),
                ('is_locked', models.BooleanField(default=False)),
                ('shareable', models.BooleanField(default=False)),
                ('grid_type', models.CharField(default=b'single', max_length=20, choices=[(b'single', b'Single Image'), (b'grid', b'Grid'), (b'slideshow', b'Slideshow'), (b'cover', b'Cover')])),
                ('grid_size', models.IntegerField(default=3)),
                ('cover_content_title', models.TextField(blank=True)),
                ('cover_content_subtitle', models.TextField(blank=True)),
                ('cover_size_title', models.PositiveIntegerField(default=18)),
                ('cover_text_alignment_title', models.CharField(default=b'l', max_length=1, choices=[(b'l', b'left'), (b'r', b'right'), (b'c', b'center')])),
                ('cover_size_subtitle', models.PositiveIntegerField(default=18)),
                ('cover_text_alignment_subtitle', models.CharField(default=b'l', max_length=1, choices=[(b'l', b'left'), (b'r', b'right'), (b'c', b'center')])),
                ('full_size', models.BooleanField(default=False)),
                ('caption', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin, publet.projects.models.DirtyMixin),
        ),
        migrations.CreateModel(
            name='Preset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('should_appear_in_output', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='PresetItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('block_class_name', models.CharField(max_length=255, choices=[(b'photo', b'PhotoBlock'), (b'text', b'TextBlock'), (b'video', b'VideoBlock'), (b'audio', b'AudioBlock')])),
                ('order', models.IntegerField(default=-1)),
            ],
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(unique=True, max_length=255, blank=True)),
                ('status', models.CharField(default=b'hidden', max_length=20, choices=[(b'hidden', b'Hidden'), (b'preorder', b'Pre-order'), (b'live', b'Published'), (b'custom', b'Custom')])),
                ('uuid', uuidfield.fields.UUIDField(max_length=32, unique=True, null=True, editable=False, blank=True)),
                ('domain', models.CharField(max_length=255, null=True, blank=True)),
                ('hosted_password', models.CharField(max_length=255, null=True, blank=True)),
                ('price', models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)),
                ('ga_campaign_id', models.CharField(max_length=5, blank=True)),
                ('mailchimp_campaign_id', models.CharField(max_length=255, blank=True)),
                ('custom_publication_origin_url', models.CharField(max_length=255, blank=True)),
                ('keywords', models.TextField(blank=True)),
                ('pagination', models.CharField(default=b'c', max_length=1, choices=[(b'c', b'Continuous'), (b'h', b'Chapters')])),
                ('published', models.DateTimeField(null=True, blank=True)),
                ('topics', models.TextField(blank=True)),
                ('content_type', models.CharField(max_length=255, blank=True)),
                ('featured', models.BooleanField(default=False)),
                ('thumbnail_url', models.CharField(max_length=255, blank=True)),
                ('gate_type', models.CharField(default=b'n', max_length=1, choices=[(b'n', b'No gate'), (b'd', b'Delayed'), (b'o', b'Non-strict'), (b's', b'Strict'), (b'1', b'1')])),
                ('default_gate_copy', models.TextField(null=True, blank=True)),
                ('embed_parent_page', models.CharField(max_length=255, blank=True)),
                ('enable_image_links', models.BooleanField(default=False)),
                ('original_pdf_link', models.CharField(max_length=255, null=True, blank=True)),
                ('original_pdf_filename', models.CharField(max_length=255, null=True, blank=True)),
                ('read_more', models.CharField(max_length=255, null=True, blank=True)),
                ('json', django_pgjson.fields.JsonField(null=True, blank=True)),
                ('nav', django_pgjson.fields.JsonField(null=True, blank=True)),
                ('toc', models.BooleanField(default=False)),
                ('new_style', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin, publet.common.models.CDNMixin),
        ),
        migrations.CreateModel(
            name='PublicationSlug',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('slug', models.SlugField(unique=True, max_length=255, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='PublicationSocialGateEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('block_id', models.IntegerField(null=True, blank=True)),
                ('block_type', models.CharField(default=b'', max_length=10, blank=True)),
                ('email', models.EmailField(max_length=254)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('referrer', models.CharField(max_length=255, blank=True)),
                ('anonymous_id', models.CharField(max_length=255, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Readability',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('url', models.CharField(max_length=255)),
                ('is_processed', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='TextBlock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('size', models.PositiveIntegerField(null=True, blank=True)),
                ('line_height', models.CharField(max_length=10, blank=True)),
                ('meta', models.CharField(max_length=1000, blank=True)),
                ('custom_css_classes', models.CharField(max_length=255, blank=True)),
                ('alignment', models.CharField(blank=True, max_length=1, choices=[(b'0', b'Column'), (b'1', b'Full'), (b'2', b'Breaking'), (b'3', b'Breaking left'), (b'4', b'Breaking right'), (b'5', b'Margin left'), (b'6', b'Margin right'), (b'7', b'Column left'), (b'8', b'Column right')])),
                ('text_alignment', models.CharField(blank=True, max_length=1, choices=[(b'l', b'left'), (b'r', b'right'), (b'c', b'center')])),
                ('order', models.IntegerField(default=-1)),
                ('is_locked', models.BooleanField(default=False)),
                ('shareable', models.BooleanField(default=False)),
                ('content', models.TextField(default=b' ')),
                ('list_style', models.CharField(default=b'disc', max_length=20, choices=[(b'disc', b'disc'), (b'circle', b'circle'), (b'square', b'square'), (b'decimal', b'decimal'), (b'decimal-leading-zero', b'decimal-leading-zero'), (b'lower-roman', b'lower-roman'), (b'upper-roman', b'upper-roman'), (b'lower-greek', b'lower-greek'), (b'lower-latin', b'lower-latin'), (b'upper-latin', b'upper-latin'), (b'armenian', b'armenian'), (b'georgian', b'georgian'), (b'lower-alpha', b'lower-alpha'), (b'upper-alpha', b'upper-alpha'), (b'none', b'none')])),
                ('is_bullets', models.BooleanField(default=False)),
                ('is_embed', models.BooleanField(default=False)),
                ('is_indented', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin, publet.projects.models.DirtyMixin),
        ),
        migrations.CreateModel(
            name='Theme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(unique=True, max_length=255, blank=True)),
                ('default_h1', models.CharField(default=b'3.75em', help_text=b"font_size line_height; e.g. '16px 24px' Use 'default' for the browser default.", max_length=255)),
                ('default_h2', models.CharField(default=b'1.5em', help_text=b"font_size line_height; e.g. '16px 24px' Use 'default' for the browser default.", max_length=255)),
                ('default_h3', models.CharField(default=b'1.3125em', help_text=b"font_size line_height; e.g. '16px 24px' Use 'default' for the browser default.", max_length=255)),
                ('default_h4', models.CharField(default=b'1.125em', help_text=b"font_size line_height; e.g. '16px 24px' Use 'default' for the browser default.", max_length=255)),
                ('default_h5', models.CharField(default=b'1.125em', help_text=b"font_size line_height; e.g. '16px 24px' Use 'default' for the browser default.", max_length=255)),
                ('default_h6', models.CharField(default=b'1.125em', help_text=b"font_size line_height; e.g. '16px 24px' Use 'default' for the browser default.", max_length=255)),
                ('default_a', models.CharField(default=b'default default', help_text=b"color text-decoration; e.g. '#000 underline' Use 'default' for the browser default", max_length=255)),
                ('default_a_visited', models.CharField(default=b'default default', help_text=b"color text-decoration; e.g. '#000 underline' Use 'default' for the browser default", max_length=255)),
                ('default_a_hover', models.CharField(default=b'default default', help_text=b"color text-decoration; e.g. '#000 underline' Use 'default' for the browser default", max_length=255)),
                ('default_a_active', models.CharField(default=b'default default', help_text=b"color text-decoration; e.g. '#000 underline' Use 'default' for the browser default", max_length=255)),
                ('default_a_focus', models.CharField(default=b'default default', help_text=b"color text-decoration; e.g. '#000 underline' Use 'default' for the browser default", max_length=255)),
                ('body_font_family', models.CharField(default=b"'Open Sans', sans-serif", max_length=255, blank=True)),
                ('heading_font_family', models.CharField(default=b"'Open Sans', sans-serif", max_length=255, blank=True)),
                ('logo', models.FileField(max_length=1000, null=True, upload_to=b'themes', blank=True)),
                ('background_image', models.FileField(null=True, upload_to=b'themes', blank=True)),
                ('toc_font', models.CharField(default=b"'Oswald', sans-serif", max_length=255, blank=True)),
                ('css', models.TextField(blank=True)),
                ('javascript', models.TextField(blank=True)),
            ],
            options={
                'permissions': (('update_theme_on_disk', 'Update theme on disk'),),
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('pagination', models.CharField(default=b'c', max_length=1, choices=[(b'c', b'Continuous'), (b'h', b'Chapters')])),
            ],
            options={
                'verbose_name_plural': 'type',
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='VideoBlock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('size', models.PositiveIntegerField(null=True, blank=True)),
                ('line_height', models.CharField(max_length=10, blank=True)),
                ('meta', models.CharField(max_length=1000, blank=True)),
                ('custom_css_classes', models.CharField(max_length=255, blank=True)),
                ('alignment', models.CharField(blank=True, max_length=1, choices=[(b'0', b'Column'), (b'1', b'Full'), (b'2', b'Breaking'), (b'3', b'Breaking left'), (b'4', b'Breaking right'), (b'5', b'Margin left'), (b'6', b'Margin right'), (b'7', b'Column left'), (b'8', b'Column right')])),
                ('text_alignment', models.CharField(blank=True, max_length=1, choices=[(b'l', b'left'), (b'r', b'right'), (b'c', b'center')])),
                ('order', models.IntegerField(default=-1)),
                ('is_locked', models.BooleanField(default=False)),
                ('shareable', models.BooleanField(default=False)),
                ('video_url', models.CharField(max_length=255)),
                ('width', models.PositiveIntegerField(null=True, blank=True)),
                ('height', models.PositiveIntegerField(null=True, blank=True)),
                ('preview', models.CharField(max_length=255, blank=True)),
                ('crop_marks', models.CharField(max_length=200, blank=True)),
                ('caption', models.TextField(blank=True)),
                ('article', models.ForeignKey(blank=True, to='projects.Article', null=True)),
                ('color', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='projects.Color', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, publet.common.models.ModelDiffMixin, publet.projects.models.DirtyMixin, publet.projects.models.CropMixin, publet.common.models.CDNMixin),
        ),
    ]
