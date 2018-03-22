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
import json
import re
import os
import zipfile
import csv
import logging
import datetime
from operator import attrgetter
from StringIO import StringIO
from urlparse import urlparse
from urllib import quote_plus
from shutil import copyfile, rmtree
from itertools import count, izip, groupby, ifilter
from subprocess import call

import requests
import tinycss2
import redis
from bleach import clean
import jsonpatch
from django_pgjson.fields import JsonField

from django.conf import settings
from django.core.cache import cache
from django.db import models, transaction, connection
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.templatetags.static import static
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse, resolve
from django.utils.safestring import mark_safe
from django.utils.html import strip_tags
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from annoying.functions import get_object_or_None

from publet.common.models import BaseModel, CDNMixin
from publet.common.fields import FilePickerField
from publet.fonts.models import Font
from publet.groups.models import Group
from publet.utils.utils import (
    slugify_uniquely, get_filepicker_read_policy, cd, chmod_recursive,
    upload_file_to_filepicker, slugify_with_hash, DatetimeJSONEncoder,
    int_to_string
)
from publet.utils.encode import decode
from publet.utils.metrics import Timer, Meter, time_as
from publet.utils.db import no_queries_allowed
from publet.utils.fn import merge, some, flatten
from uuidfield import UUIDField

from publet.projects import tasks
from publet.projects import parse
from publet.projects.validate import validate_article, validate_theme
from publet.projects.search import get_es
from publet.projects.react import (
    get_article_html, get_article_document, upload_article_document,
    get_scroll_publication_document
)
from publet.projects.pdf.core import (
    parse_pdf_from_xml, Text as PDFText, Photo as PDFPhoto
)
from publet.third.tasks import submit_to_integration

User = settings.USER_MODEL

logger = logging.getLogger(__name__)
r = redis.StrictRedis(db=0)

lua = """
local k = redis.call('keys', ARGV[1])
if next(k) == nil then
    return nil
else
    return redis.call('del', unpack(k))
end
"""
invalidate_publication_in_redis = r.register_script(lua)

FILEPICKER_READ_POLICY, FILEPICKER_READ_SIGNATURE = \
    get_filepicker_read_policy()

STATIC_ROOT = getattr(settings, 'STATIC_ROOT', None)
MEDIA_URL = getattr(settings, 'MEDIA_URL', None)
BASE_PATH = getattr(settings, 'BASE_PATH', None)
HOST = getattr(settings, 'HOST', None)
SHORT_HOST = getattr(settings, 'SHORT_HOST', None)
TESTING = getattr(settings, 'TESTING', None)
PDF_GENERATION_BIN = getattr(settings, 'PDF_GENERATION_BIN', None)
IMAGE_GENERATION_BIN = getattr(settings, 'IMAGE_GENERATION_BIN', None)
ARTICLE_EDITOR_BASE_URL = getattr(settings, 'ARTICLE_EDITOR_BASE_URL', None)
PREVIEW_URL = getattr(settings, 'PREVIEW_URL', None)
SETTINGS_URL = getattr(settings, 'SETTINGS_URL', '')


LIST_STYLE_TYPE_OPTIONS = (
    ('disc', 'disc',),
    ('circle', 'circle',),
    ('square', 'square',),
    ('decimal', 'decimal',),
    ('decimal-leading-zero', 'decimal-leading-zero',),
    ('lower-roman', 'lower-roman',),
    ('upper-roman', 'upper-roman',),
    ('lower-greek', 'lower-greek',),
    ('lower-latin', 'lower-latin',),
    ('upper-latin', 'upper-latin',),
    ('armenian', 'armenian',),
    ('georgian', 'georgian',),
    ('lower-alpha', 'lower-alpha',),
    ('upper-alpha', 'upper-alpha',),
    ('none', 'none',),
)


STATUSES = (
    ('hidden', 'Hidden'),
    ('preorder', 'Pre-order'),
    ('live', 'Published'),
    ('custom', 'Custom'),
)


ALIGNMENT_CHOICES = (
    ('0', 'Column',),
    ('1', 'Full',),
    ('2', 'Breaking',),
    ('3', 'Breaking left',),
    ('4', 'Breaking right',),
    ('5', 'Margin left',),
    ('6', 'Margin right',),
    ('7', 'Column left',),
    ('8', 'Column right',),
)

TEXT_ALIGNMENT_CHOICES = (
    ('l', 'left',),
    ('r', 'right',),
    ('c', 'center',),
)


PAGINATION_CHOICES = (
    ('c', 'Continuous',),
    ('h', 'Chapters',),
)

TOC_ARTICLE_NAME = 'Table of Contents'

FLAVOR_TYPES = (
    ('text', 'Text',),
    ('photo', 'Photo',),
    ('audio', 'Audio',),
    ('video', 'Video',),
)

GATE_TYPES = (
    ('n', 'No gate',),
    ('d', 'Delayed',),
    ('o', 'Non-strict',),
    ('s', 'Strict',),
    ('1', '1',),
)


AVAILABLE_BLOCKS_CLASSES = (
    ('photo', 'PhotoBlock',),
    ('text', 'TextBlock',),
    ('video', 'VideoBlock',),
    ('audio', 'AudioBlock',),
)


def get_width_and_height_from_filepicker(image_url):
    id = image_url.split('/')[-1]

    url = ("https://www.filepicker.io/api/file/{id}/metadata?"
           "policy={policy}&signature={signature}&width=true&height=true")

    url = url.format(**{
        'id': id,
        'policy': FILEPICKER_READ_POLICY,
        'signature': FILEPICKER_READ_SIGNATURE
    })

    r = requests.get(url)

    if r.status_code == 200:
        return r.json()

    if r.status_code == 404:
        return

    raise ValueError('Server error {} - {}'.format(r.status_code, r.content))


def ext_call(*args, **kwargs):
    if TESTING:
        return 0
    return call(*args, **kwargs)


def get_block_type(type_string):
    if type_string in ['t', 'text']:
        return TextBlock
    elif type_string in ['g', 'gallery', 'p', 'photo']:
        return PhotoBlock
    elif type_string in ['a', 'audio']:
        return AudioBlock
    elif type_string in ['v', 'video']:
        return VideoBlock
    else:
        return None


# XXX: What even is this???
def find_block(pk):
    return (
        get_object_or_None(TextBlock, pk=pk) or
        get_object_or_None(PhotoBlock, pk=pk) or
        get_object_or_None(AudioBlock, pk=pk) or
        get_object_or_None(VideoBlock, pk=pk)
    )


def expand_social_service_name(short_name):
    if short_name == 't':
        return 'twitter'
    elif short_name == 'f':
        return 'facebook'
    elif short_name == 'l':
        return 'linkedin'
    elif short_name == 'g':
        return 'googleplus'

    return None


def download_file(url, local_filename):
    r = requests.get(url, stream=True)

    if r.status_code != 200:
        raise Exception('Download error')

    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()

    return local_filename


class Id(object):

    def __init__(self, number):
        self.number = number

    def __call__(self):
        self.number += 1
        return self.number


class SassException(Exception):
    pass


class CreatedByBlankException(Exception):
    pass


class BlockTypeMixin(object):

    def _block_types(self):
        return {
            'photo': PhotoBlock,
            'video': VideoBlock,
            'text': TextBlock,
            'audio': AudioBlock
        }


# Article models

class Type(BaseModel):
    name = models.CharField(max_length=255)
    pagination = models.CharField(max_length=1, default='c',
                                  choices=PAGINATION_CHOICES)

    class Meta:
        verbose_name_plural = 'type'

    def __unicode__(self):
        return self.name


class Theme(BaseModel):
    """
    A theme is a pre-defined set of styles for the output of a article.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, unique=True)

    fonts = models.ManyToManyField(Font, blank=True)

    group = models.ForeignKey(Group, null=True, blank=True)

    _h_help_text = ("font_size line_height; e.g. '16px 24px' Use 'default' for"
                    " the browser default.")

    default_h1 = models.CharField(max_length=255, help_text=_h_help_text,
                                  default='3.75em')
    default_h2 = models.CharField(max_length=255, help_text=_h_help_text,
                                  default='1.5em')
    default_h3 = models.CharField(max_length=255, help_text=_h_help_text,
                                  default='1.3125em')
    default_h4 = models.CharField(max_length=255, help_text=_h_help_text,
                                  default='1.125em')
    default_h5 = models.CharField(max_length=255, help_text=_h_help_text,
                                  default='1.125em')
    default_h6 = models.CharField(max_length=255, help_text=_h_help_text,
                                  default='1.125em')

    _a_help_text = ("color text-decoration; e.g. '#000 underline' Use "
                    "'default' for the browser default")
    default_a = models.CharField(max_length=255, help_text=_a_help_text,
                                 default='default default')
    default_a_visited = models.CharField(max_length=255,
                                         default='default default',
                                         help_text=_a_help_text)
    default_a_hover = models.CharField(max_length=255, help_text=_a_help_text,
                                       default='default default')
    default_a_active = models.CharField(max_length=255, help_text=_a_help_text,
                                        default='default default')
    default_a_focus = models.CharField(max_length=255,
                                       default='default default',
                                       help_text=_a_help_text)

    background_color = models.ForeignKey('Color', blank=True, null=True,
                                         related_name='background',
                                         on_delete=models.SET_NULL)
    link_color = models.ForeignKey('Color', blank=True, null=True,
                                   related_name='link',
                                   on_delete=models.SET_NULL)

    heading_color = models.ForeignKey('Color', blank=True, null=True,
                                      related_name='heading',
                                      on_delete=models.SET_NULL)
    header_color = models.ForeignKey('Color', blank=True, null=True,
                                     related_name='header',
                                     on_delete=models.SET_NULL)
    nav_font_color = models.ForeignKey('Color', blank=True, null=True,
                                       related_name='nav_bg',
                                       on_delete=models.SET_NULL)
    nav_background_color = models.ForeignKey('Color', blank=True, null=True,
                                             related_name='nav',
                                             on_delete=models.SET_NULL)

    body_font_family = models.CharField(max_length=255, blank=True,
                                        default="'Open Sans', sans-serif")
    heading_font_family = models.CharField(max_length=255, blank=True,
                                           default="'Open Sans', sans-serif")

    logo = models.FileField(upload_to='themes', null=True, blank=True,
                            max_length=1000)
    background_image = models.FileField(upload_to='themes', null=True,
                                        blank=True)

    toc_color = models.ForeignKey('Color', blank=True, null=True,
                                  related_name='toc_font_color',
                                  on_delete=models.SET_NULL)

    toc_background_color = models.ForeignKey('Color', blank=True, null=True,
                                             related_name='toc_background',
                                             on_delete=models.SET_NULL)

    toc_font = models.CharField(max_length=255, blank=True,
                                default="'Oswald', sans-serif")

    css = models.TextField(blank=True)
    javascript = models.TextField(blank=True)

    class Meta:
        permissions = (
            ('update_theme_on_disk', 'Update theme on disk',),
        )

    def __unicode__(self):
        return self.name

    def safe_css(self):
        """
        Attempt to parse self.css for valid css;  return value will
        still need to be marked as safe in the template
        """
        if not self.css:
            return ''

        # TODO: Disallow body styles
        parsed = tinycss2.parse_stylesheet(self.css)

        if some(lambda x: x.type == 'error', parsed):
            return ''

        return self.css

    @property
    def theme_dir(self):
        return os.path.join(BASE_PATH, 'static/css/outputs')

    @property
    def theme_dir_path(self):
        if self.is_checked_in():
            return os.path.join(self.theme_dir, self.slug)
        else:
            return os.path.join(self.theme_dir, 'generated', self.slug)

    @property
    def theme_file_path(self):
        return os.path.join(self.theme_dir_path, 'theme.scss')

    @property
    def theme_script_file_path(self):
        return os.path.join(self.theme_dir_path, 'scripts-browser.js')

    @property
    def base_theme_dir_path(self):
        return os.path.join(BASE_PATH, 'static/css/outputs/base')

    def ensure_theme_on_disk(self):
        if os.path.exists(self.theme_dir_path):
            rmtree(self.theme_dir_path)

        os.makedirs(self.theme_dir_path)
        chmod_recursive(self.theme_dir_path, 0775)

    def write_scss(self):
        theme_file = render_to_string('themes/theme_scss.html', {
            'theme': self,
            'MEDIA_URL': MEDIA_URL
        })

        with open(self.theme_file_path, 'w') as f:
            f.write(theme_file)

        cmd = '/usr/local/bin/sass theme.scss:style-browser.css'

        with cd(self.theme_dir_path):
            exit_code = ext_call(cmd, shell=True)

        if exit_code > 0:
            raise SassException('Theme {}'.format(self.pk))

        chmod_recursive(self.theme_dir_path, 0775)

    def write_script(self):
        if not self.javascript:
            return

        with open(self.theme_script_file_path, 'w') as f:
            f.write(self.javascript)

    def update_theme_on_disk(self, collect_static=True):
        if self.is_checked_in():
            return

        self.ensure_theme_on_disk()
        self.write_scss()
        self.write_script()

        if collect_static:
            tasks.collectstatic.delay()
            self.invalidate_html_cache_for_publications()

    def disassociate(self):
        self.fonts.clear()
        self.color_set.clear()

        fields = filter(lambda x: x.endswith('_set'), dir(self))

        for f in fields:
            qs = getattr(self, f).all()
            qs.update(theme=None)

    def is_checked_in(self):
        if not hasattr(self, '_is_checked_in'):
            outputs_dir = os.path.join(BASE_PATH, 'static/css/outputs')
            self._is_checked_in = self.slug in os.listdir(outputs_dir)

        return self._is_checked_in

    def add_default_flavors(self):
        Flavor.create_default_body(self)
        Flavor.create_default_header(self)
        Flavor.create_default_sub_header(self)
        Flavor.create_block_defaults(self)

    def add_default_colors(self):
        """
                                  _
        __      ____ _ _ __ _ __ (_)_ __   __ _
        \ \ /\ / / _` | '__| '_ \| | '_ \ / _` |
         \ V  V / (_| | |  | | | | | | | | (_| |
          \_/\_/ \__,_|_|  |_| |_|_|_| |_|\__, |
                                           |___/

        This **cannot** be called in the `save` method because then
        django-tastypie will just clear it out on create.  Don't ask
        why.
        """
        Color.create_default_colors(self)

    def add_default_fonts(self):
        """
                                  _
        __      ____ _ _ __ _ __ (_)_ __   __ _
        \ \ /\ / / _` | '__| '_ \| | '_ \ / _` |
         \ V  V / (_| | |  | | | | | | | | (_| |
          \_/\_/ \__,_|_|  |_| |_|_|_| |_|\__, |
                                           |___/

        This **cannot** be called in the `save` method because then
        django-tastypie will just clear it out on create.  Don't ask
        why.
        """
        self.fonts.add(*Font.create_default_fonts())

    @classmethod
    def create_default_theme_for_group(cls, group):
        t = cls(name='Default', group=group)
        t.save(update_on_disk=False)
        t.create_defaults()
        t.update_theme_on_disk()
        return t

    def create_defaults(self):
        """
        To be called after save;  it cannot live in the save() method
        because tastypie would just ignore it
        """
        self.add_default_colors()
        self.add_default_fonts()
        self.add_default_flavors()

        colors = self.get_colors()

        self.background_color = colors.get(hex='ffffff')
        self.link_color = colors.get(hex='1C4382')
        self.nav_background_color = colors.get(hex='000000')
        self.nav_font_color = colors.get(hex='ffffff')

        self.header_color = colors.get(hex='333333')
        self.heading_color = colors.get(hex='1C4382')

        self.save(update_on_disk=False)

        return self

    def duplicate(self):
        new_kwargs = []
        ignore = ['id', 'uuid', 'slug', 'modified', 'created']

        for field in self._meta.fields:
            if field.name in ignore:
                continue

            new_kwargs.append((field.name, getattr(self, field.name)))

        kwargs = dict(new_kwargs)

        with transaction.atomic():
            new_theme = self.__class__(**kwargs)
            new_theme.save(update_on_disk=False)

            fonts = []

            for font in self.fonts.all():
                f = font.duplicate(parent=new_theme)
                fonts.append(f)

            for color in self.get_colors().all():
                color.duplicate(parent=new_theme)

            new_theme.fonts.add(*fonts)

        new_theme.update_theme_on_disk()

        return new_theme

    def copy_to_group(self, group):
        theme = self.duplicate()
        theme.group = group
        theme.save(update_on_disk=False)
        return theme

    def invalidate_html_cache_for_publications(self):
        publications = self.publication_set.all()

        for publication in publications:
            publication.invalidate_html_cache()

    def get_colors(self):
        return self.color_set.all()

    def get_color_fields(self):
        def is_color(f):
            return isinstance(f, models.ForeignKey) and f.rel.to == Color

        return filter(is_color, self._meta.fields)

    def save(self, *args, **kwargs):
        update_on_disk = kwargs.pop('update_on_disk', True)

        if not self.slug:
            self.slug = slugify_uniquely(self.name, Theme)

        super(Theme, self).save(*args, **kwargs)

        if update_on_disk:
            tasks.update_theme_on_disk.delay(self)


class PublicationManager(models.Manager):

    def by_slug(self, slug, group_slug=None):
        slug_instance = get_object_or_None(PublicationSlug, slug=slug)

        if slug_instance:
            if group_slug:
                if slug_instance.publication.group.slug != group_slug:
                    return

            return slug_instance.publication


class Publication(BaseModel, CDNMixin):
    """
    A publication is like a magazine or book: it contains many articles
    or "chapters", which are in a specific order.

    The `type` and `theme` on a publication are simply used as defaults
    for the articles that are created within a publication.

    Field-wise they're very similar to Articles, with the important
    distinction that articles that belong to a publication are
    exclusively paired to that publication.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, unique=True)
    group = models.ForeignKey(Group)
    type = models.ForeignKey(Type, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES,
                              default='hidden')
    theme = models.ForeignKey(Theme, null=True, blank=True)
    new_theme = models.ForeignKey('NewTheme', null=True, blank=True)
    uuid = UUIDField(blank=True, null=True, max_length=32, auto=True,
                     unique=True)
    domain = models.CharField(max_length=255, null=True, blank=True)
    hosted_password = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True,
                                blank=True)
    ga_campaign_id = models.CharField(max_length=5, blank=True)
    mailchimp_campaign_id = models.CharField(max_length=255, blank=True)
    custom_publication_origin_url = models.CharField(max_length=255,
                                                     blank=True)
    keywords = models.TextField(blank=True)
    pagination = models.CharField(max_length=1, default='c',
                                  choices=PAGINATION_CHOICES)

    published = models.DateTimeField(blank=True, null=True)

    topics = models.TextField(blank=True)
    # User defined type of publication: report, white paper, etc
    content_type = models.CharField(max_length=255, blank=True)
    featured = models.BooleanField(default=False)
    thumbnail_url = models.CharField(max_length=255, blank=True)

    gate_type = models.CharField(max_length=1, choices=GATE_TYPES, default='n')
    default_gate_copy = models.TextField(blank=True, null=True)

    # If this publication is going to be embedded on a foreign domain, we need
    # to know what page/url it's on.
    embed_parent_page = models.CharField(max_length=255, blank=True)

    enable_image_links = models.BooleanField(default=False)
    original_pdf_link = models.CharField(max_length=255, blank=True, null=True)
    original_pdf_filename = models.CharField(max_length=255, blank=True,
                                             null=True)

    read_more = models.CharField(max_length=255, blank=True, null=True)

    json = JsonField(null=True, blank=True)
    nav = JsonField(null=True, blank=True)
    toc = models.BooleanField(default=False)

    # Does this publication use new-style articles?
    new_style = models.BooleanField(default=False)

    always_save = True

    objects = PublicationManager()

    def __init__(self, *args, **kwargs):
        super(Publication, self).__init__(*args, **kwargs)
        self._original_theme_id = self.theme_id
        self._original_type_id = self.type_id
        self._original_name = self.name
        self._original_status = self.status
        self._original_new_style = self.new_style
        self._original_domain = self.domain

    def __unicode__(self):
        return self.name

    @property
    def settings_url(self):
        return SETTINGS_URL + '/editor/#/' + str(self.pk)

    def update(self, ops):
        nav_ops = ifilter(nav_op, ops)
        nav = {
            'publication': {
                'nav': self.nav or self.default_nav
            }
        }
        proposed_data = jsonpatch.apply_patch(nav, nav_ops)
        proposed_data = proposed_data['publication']['nav']

        self.nav = proposed_data
        self.save()

    @property
    def default_nav(self):
        return {
            'navType': 'horizontal',
            'enabled': True,
            'fixed': False,
            'background': '#1C4382',
            'textColor': 'white',
            'textColorHover': '#D59439',
            'caption': '',
            'style': {
                'borderBottom': '12px solid #D59439'
            },
            'gate': {
                'content': {
                    'body': 'Default body',
                    'header': 'Sign up now to read more',
                    'title': 'Lolcats Quarterly'
                },
                'enabled': False,
                'form': {
                    'cta': {
                        'label': 'Get me my Lolcats',
                        'style': {
                            'backgroundColor': 'darkslategrey',
                            'borderRadius': '4px',
                            'color': 'silver'
                        }
                    },
                    'inputs': [
                        {
                            'label': 'First Name',
                            'type': 'text',
                            'width': 'half'
                        },
                        {
                            'label': 'Last Name',
                            'type': 'text',
                            'width': 'half'
                        },
                        {
                            'label': 'Job Title',
                            'type': 'text',
                            'width': 'full'
                        },
                        {
                            'label': 'Email',
                            'type': 'email',
                            'width': 'full'
                        }
                    ]
                },
                'navButton': {
                    'label': 'Call to Action!',
                    'style': {
                        'backgroundColor': 'darkslategrey',
                        'color': 'silver'
                    }
                }
            }
        }

    @property
    def es_mapping(self):
        return {
            "mappings": {
                "block": {
                    "properties": {
                        "created": {
                            "type": "date",
                            "format": "dateOptionalTime"
                        },
                        "name": {
                            "type": "string",
                            "analyzer": "english"
                        },
                        "keywords": {
                            "type": "string",
                            "analyzer": "english"
                        },
                        "topics": {
                            "type": "string",
                            "analyzer": "english"
                        },
                        "group_id": {
                            "type": "long"
                        },
                        "publication_id": {
                            "type": "long"
                        },
                        "id": {
                            "type": "long"
                        }
                    }
                }
            }
        }

    def es_doc(self):
        return {
            'created': self.created,
            'name': self.name,
            'keywords': self.keywords,
            'topics': self.topics,
            'group_id': self.group.pk,
            'publication_id': self.pk
        }

    @property
    def rest_api_url(self):
        return reverse('api-publication-detail', args=(self.pk,))

    def articles(self):
        if self.new_style:
            return self.newarticle_set
        else:
            return self.article_set

    @property
    def thumbnail(self):
        return self.thumbnail_url or \
            reverse('publication-thumbnail',
                    args=(self.group.slug, self.slug)) or \
            static('img/default-publication-broker.png')

    def get_gate_class(self):
        if self.new_style:
            return GateSubmission
        else:
            return PublicationSocialGateEntry

    @property
    def get_cache_key_html(self, page=1, is_mobile=False,
                           is_custom_domain=False):
        ui = 'mobile' if is_mobile else 'desktop'
        domain = 'custom' if is_custom_domain else 'publet'
        return 'publication:{}:{}:html:{}:{}'.format(
            self.pk, page, domain, ui)

    def invalidate_html_cache(self):
        # The '0' is hardcoded here and in the settings.  It refers to
        # the DB number.  Note that this atomically deletes all cached
        # pages in the publication.
        wildcard_key = ':0:publication:{}:*'.format(self.pk)
        invalidate_publication_in_redis(args=[wildcard_key])

    @property
    def analytics_slug(self):
        return '/'.join([self.group.slug, self.slug])

    @property
    def theme_stylesheet_url(self):
        if self.theme:
            if self.theme.is_checked_in():
                slug = self.theme.slug
            else:
                slug = os.path.join('generated', self.theme.slug)
        else:
            slug = 'base'
        return 'css/outputs/{}/style-browser.css'.format(slug)

    @property
    def presets(self):
        return Preset.objects.filter(
            Q(publication_type__publication=self) |
            Q(name='Blank')).exclude(name='Splash')

    def get_custom_publication_path(self):
        return "/opt/publet/custom/{}".format(self.slug)

    def _update_custom_publication_data(self):
        path = self.get_custom_publication_path()

        if not os.path.exists(path):
            cmds = ['git clone {} {}'.format(
                self.custom_publication_origin_url, path)]
        else:
            cmds = ['git --git-dir={}/.git fetch'.format(path),
                    'git --git-dir={}/.git --work-tree={} merge '
                    'origin/master'.format(path, path)]

        for cmd in cmds:
            ext_call(cmd, shell=True)

    def update_custom_publication_data(self):
        return tasks.republish_publication.delay(self)

    def get_splash_article(self):
        try:
            return self.article_set.filter(preset__name='Splash')[0]
        except IndexError:
            return None

    def get_articles(self):
        return self.article_set.filter(is_draft=False).filter(
            Q(preset__should_appear_in_output=True) |
            Q(preset__isnull=True)).order_by('order')

    def get_new_articles(self):
        return self.newarticle_set.all().order_by('order')

    def get_article_count(self):
        return self.get_articles().count()

    def get_absolute_url(self):
        return '{}/groups/{}/publications/{}/'.format(HOST,
                                                      self.group.slug,
                                                      self.slug)

    def get_quoted_absolute_url(self):
        return quote_plus(self.get_absolute_url())

    def get_new_style_preview_url(self):
        return '{}/{}/{}/'.format(PREVIEW_URL, self.group.slug, self.slug)

    def get_share_url(self):
        """
        Return sharing url suitable for social media
        """
        if self.embed_parent_page:
            return self.embed_parent_page

        if self.new_style:
            return self.get_new_style_preview_url()

        if self.domain:
            d = self.domain
            if not d.startswith('http'):
                d = 'http://' + d
            return d

        if self.group.domain:
            d = self.group.domain

            if not d.startswith('http'):
                d = 'http://' + d

            return '{}/{}/'.format(d, self.slug)

        args = (self.group.slug, self.slug)
        return HOST + reverse('preview-publication-html', args=args)

    def get_draft_preview_url(self):
        args = (self.group.slug, self.slug)
        return HOST + reverse('preview-publication-html', args=args) + '?draft'

    def get_quoted_share_url(self):
        return quote_plus(self.get_share_url())

    def get_css_template(self):
        return '{}/css/outputs/{}/{}/style.css'.format(
            settings.STATIC_ROOT,
            slugify(self.type.name),
            slugify(self.theme.name))

    def get_html_template(self):
        return 'outputs/publication.html'

    def get_heatmap_template(self):
        return 'outputs/publication.html'

    def get_splash_template(self):
        return 'outputs/publication-splash.html'

    def get_mobile_css_template(self):
        return '{}/css/outputs/mobile/style.css'.format(
            settings.STATIC_ROOT,
            slugify(self.type.name),
            slugify(self.theme.name))

    def get_mobile_html_template(self):
        return 'outputs/mobile.html'

    def get_render_dir(self):
        renders_dir = os.path.join(BASE_PATH, 'renders', 'publications')
        publication_dir = '{}/{}'.format(renders_dir, self.slug)

        if not os.path.exists(publication_dir):
            os.makedirs(publication_dir)

        subs = ['screenshots', 'pdfs']

        for sub in subs:
            s = os.path.join(publication_dir, sub)

            if not os.path.exists(s):
                os.makedirs(s)

        return publication_dir

    def get_screenshot_dir(self):
        return os.path.join(self.get_render_dir(), 'screenshots')

    def get_latest_screenshot(self):
        screenshot_dir = self.get_screenshot_dir()
        files = os.listdir(screenshot_dir)
        files.reverse()

        try:
            latest = files[0]
            return os.path.join(self.get_screenshot_dir(), latest)
        except IndexError:
            return

    def _render_css(self):

        css_dir = '{}/html/css'.format(self.get_render_dir())

        if not os.path.exists(css_dir):
            os.makedirs(css_dir)

        base = 'static/css/outputs/generated'
        theme_slug = self.theme.slug

        files = [
            'style-browser.css',
            '../../shared/glyphicons.css',
            '../../shared/glyphicons-regular.woff',
            '../../shared/glyphicons-regular.ttf',
            '../../shared/glyphicons-regular.svg',
            '../../shared/skeleton.css',
            '../../shared/logo.png',
            '../../shared/flexslider.css',
            '../../shared/magnific-popup.css',
            '../../shared/HelveticaLTStd-BoldCond.otf',
            '../../shared/HelveticaLTStd-LightCond.otf',
            '../../shared/HelveticaLTStd-LightCondObl.otf',
            '../../shared/twitter.png',
            '../../shared/toc-sprite.png',
        ]
        for f in files:
            full_src = '/'.join([BASE_PATH, base, theme_slug, f])
            full_dst = '/'.join([css_dir, os.path.basename(f)])
            copyfile(full_src, full_dst)

        return True

    def _render_js(self):
        # TODO: Currently does nothing; js files can be plugged in the
        #       "files" variable

        js_dir = '{}/html/js'.format(self.get_render_dir())

        if not os.path.exists(js_dir):
            os.makedirs(js_dir)

        files = []

        for f in files:
            full_src = '/'.join([BASE_PATH, f])
            full_dst = '/'.join([js_dir, os.path.basename(f)])
            copyfile(full_src, full_dst)

    def _render_html(self):

        html_dir = '{}/html'.format(self.get_render_dir())

        if not os.path.exists(html_dir):
            os.makedirs(html_dir)

        rendered_html = render_to_string(self.get_html_template(), {
            'publication': self,
            'pagination': 'c',  # force to continuous in static mode
            'static_mode': True
        })

        with open('{}/index.html'.format(html_dir), 'w+') as html:
            html.write(rendered_html.encode('utf-8'))

    def _render_mobile_html_and_css(self):

        html_dir = '{}/mobile-html'.format(self.get_render_dir())

        if not os.path.exists(html_dir):
            os.makedirs(html_dir)

        css_dir = '{}/mobile-html/css'.format(self.get_render_dir())

        if not os.path.exists(css_dir):
            os.makedirs(css_dir)

        with open(self.get_mobile_css_template(), 'r') as css_file:
            rendered_css = css_file.read()

        with open('{}/style.css'.format(css_dir), 'w+') as css:
            css.write(rendered_css)

        rendered_html = render_to_string(self.get_mobile_html_template(), {
            'publication': self
        })

        with open('{}/index.html'.format(html_dir), 'w+') as html:
            html.write(rendered_html.encode('utf-8'))

    def _render_html_zip(self):
        html_dir = '{}/html'.format(self.get_render_dir())
        path = self.filename_for_format('zip')

        zip_file = zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED)

        rootlen = len(html_dir) + 1
        for base, dirs, files in os.walk(html_dir):
            for file in files:
                fn = os.path.join(base, file)
                zip_file.write(fn, fn[rootlen:])

        zip_file.close()

    def render_html_zip(self):
        with Timer('publication-render-html'):
            return tasks.generate_html_zip.delay(self)

    def _render_epub(self):

        cmd = 'sudo {} {}/mobile-html/index.html {} --no-default-epub-cover'
        cmd = cmd.format(settings.EPUB_GENERATION_BIN,
                         self.get_render_dir(),
                         self.filename_for_format('epub'))

        code = ext_call(cmd, shell=True)

        logger.info('epub render - publication: {} - return: {}'.format(
            self.pk, code))

        return code

    def render_epub(self):
        with Timer('publication-render-epub'):
            return tasks.generate_epub.delay(self)

    def _render_mobi(self):
        code = ext_call('sudo {} {}/mobile-html/index.html {}'.format(
            settings.EPUB_GENERATION_BIN,
            self.get_render_dir(),
            self.filename_for_format('mobi')), shell=True)

        logger.info('mobi render - publication: {} - return: {}'.format(
            self.pk, code))

        return code

    def render_mobi(self):
        with Timer('publication-render-mobi'):
            return tasks.generate_mobi.delay(self)

    def _render_pdf(self):
        # TODO: Sync methods should also render dependencies
        code = ext_call(
            'sudo {} --print-media-type {}/html/index.html {}'.format(
                PDF_GENERATION_BIN, self.get_render_dir(),
                self.filename_for_format('pdf')), shell=True)

        logger.info('pdf render - publication: {} - return: {}'.format(
            self.pk, code))

        return code

    def _render_jpg(self):
        code = ext_call(
            '{} --width 1200 --crop-h 700 --format jpg '
            '-n {}/html/index.html {}'.format(
                IMAGE_GENERATION_BIN, self.get_render_dir(),
                self.filename_for_format('jpg')), shell=True)

        logger.info('screenshot render - publication: {} - return: {}'.format(
            self.pk, code))

        return code

    def render_jpg(self):
        with Timer('publication-render-jpg'):
            return tasks.generate_jpg.delay(self)

    def render_pdf(self):
        with Timer('publication-render-pdf'):
            return tasks.generate_pdf.delay(self)

    def render_ios(self):
        logger.error('no longer supported')

    def reorder(self, article_ids):
        """
        Reorder all of the articles in a publication given a list of
        article ids, return the new ordering as `{id: order}`.
        """
        order_iter = count()
        ordering = dict(izip(article_ids, order_iter))
        with transaction.atomic():
            for article in self.articles().all():
                try:
                    order = ordering[article.id]
                except KeyError:
                    order = next(order_iter)
                    ordering[article.id] = order
                if article.order != order:
                    article.order = order
                    article.save(update_fields=['order'])

        if self.new_style:
            tasks.upload_new_publication.delay(self.pk)

        return ordering

    def duplicate(self, prepend_copy=True):
        """
        Duplicate the publication and return the new instance.
        Duplicates the entire publication tree including articles and
        article blocks.

        ``prepend_copy`` determines if the new publication name should
        be altered
        """
        new_kwargs = []

        ignore = ['id', 'uuid', 'slug', 'modified', 'created']

        for field in self._meta.fields:
            if field.name in ignore:
                continue

            new_kwargs.append((field.name, getattr(self, field.name)))

        kwargs = dict(new_kwargs)

        if prepend_copy:
            kwargs['name'] = 'Copy of %s' % kwargs['name']

        kwargs['status'] = 'hidden'
        kwargs['domain'] = None

        with Timer('publication-duplication'):

            with transaction.atomic():
                new_publication = self.__class__(**kwargs)
                new_publication.save(duplicate=True)

                for article in self.articles().all().order_by('order'):
                    article.duplicate(publication=new_publication)

        return new_publication

    def should_rerender(self, file_format):
        # filename = self.filename_for_format(file_format)
        # return not os.path.exists(filename)

        # TODO: Find a better rerender logic than above
        logger.info('publications always rerender')
        return True

    def filename_for_format(self, file_format):
        if file_format == 'ios':
            file_format = 'ipa'

        d = ''

        if file_format == 'jpg':
            d = 'screenshots'

        return os.path.join(self.get_render_dir(), d,
                            self.base_filename_for_format(file_format))

    def base_filename_for_format(self, file_format):
        last_modified = self.modified.strftime('%Y%m%d-%H%M%S')
        now = datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        return '%s-%s-%s.%s' % (self.slug, last_modified, now, file_format)

    def render_ext(self, ext, sync=False):
        if ext == 'zip':
            ext = 'html_zip'

        if sync:
            method_name = '_render_{}'.format(ext)
        else:
            method_name = 'render_{}'.format(ext)

        method = getattr(self, method_name)
        return method()

    def get_protected_file_url(self, ext):
        if ext == 'ios':
            ext = 'ipa'
        base_filename = '{}.{}'.format(self.slug, ext)
        return reverse('protected-publication-file',
                       kwargs=dict(publication_slug=base_filename))

    def get_protected_pdf_url(self):
        return self.get_protected_file_url('pdf')

    def has_user_already_purchased(self, user):
        if not user:
            return False

        if self.purchase_set.filter(user=user).exists():
            return True

        if self.group.purchase_set.filter(user=user).exists():
            return True

        return False

    def get_ga_tracking_code(self):
        group_id = self.group.ga_tracking_id

        if not group_id:
            return None

        return 'UA-{}-{}'.format(group_id, self.ga_campaign_id or '1')

    def get_article_titles_character_total(self):
        articles = self.get_articles()
        titles = [a.name for a in articles]
        return len(''.join(titles))

    def get_buyers(self):
        purchases = self.purchase_set.select_related().all()
        return [p.user for p in purchases]

    def export_purchases(self):
        buyers = self.get_buyers()

        f = StringIO()

        writer = csv.writer(f)
        writer.writerow(['username', 'email', 'first', 'last'])

        for user in buyers:
            writer.writerow([user.username,
                             user.email,
                             user.first_name,
                             user.last_name])

        f.seek(0)
        return f.read()

    def get_embed_code(self):
        return render_to_string('outputs/publication-embed-code.html', {
            'HOST': HOST,
            'publication': self
        })

    def get_php_embed_code(self):
        if HOST.startswith('https'):
            host = HOST.replace('https', 'http')
        else:
            host = HOST

        url = ''.join([host, reverse('render-publication-frameless',
                                     args=[self.slug])])
        return """<?php echo file_get_contents('{}'); ?>""".format(url)

    def has_draft_articles(self):
        return self.article_set.filter(is_draft=True).exists()

    def has_fixed_article_order(self):
        articles = self.get_articles()
        orders = [a.order for a in articles]
        return len(orders) == len(set(orders))

    def fix_article_order(self):
        with transaction.atomic():
            self._fix_article_order_no_transaction()

    def _fix_article_order_no_transaction(self):
        articles = self.get_articles()

        for article, index in zip(articles, range(0, len(articles))):
            article.order = index
            article.save()

    def get_blocks(self):
        return [block
                for article in self.get_articles()
                for block in article.get_blocks()]

    def save(self, *args, **kwargs):
        created = False if self.pk else True
        new_slug = False

        duplicate = kwargs.pop('duplicate', False)

        if not self.slug or (self._original_name != self.name):
            self.slug = slugify_with_hash(self.name, Publication)
            new_slug = True

        if not self.theme_id:
            self.theme = self.group.get_default_theme()

        if self.theme_id != self._original_theme_id:
            self._original_theme_id = self.theme_id
            assert self.theme in self.group.theme_set.all()

            self.article_set.update(theme=self.theme)

        if self.status != self._original_status:
            if self.status == 'live':
                self.published = datetime.datetime.now()

        if self.type and created:
            self.pagination = self.type.pagination

        if self.type_id != self._original_type_id:
            self.pagination = self.type.pagination

        if self.new_style != self._original_new_style:
            if not self.new_style:
                raise Exception('Moving to old editor is forbidden')

        if self.domain and self.domain != self._original_domain:
            if Publication.objects.filter(domain=self.domain).exists():
                raise Exception('Domain exists')

        if not self.nav:
            self.nav = self.default_nav

        if not isinstance(self.nav, dict):
            raise TypeError('Nav is not a dict')

        self.ensure_cdn_links('original_pdf_link')

        if created:

            if duplicate and not self.new_style:
                # If we're duplicating an old style pub, don't make the copy a
                # new style
                pass
            else:
                # Always new style for new publications
                if not self.new_theme:
                    self.new_theme = self.group.get_default_new_theme()
                    self.new_style = True

        obj = super(Publication, self).save(*args, **kwargs)

        if new_slug:
            PublicationSlug.objects.get_or_create(slug=self.slug,
                                                  publication=self)

        if not created:
            self.invalidate_html_cache()

        tasks.index_publication.delay(self.pk)
        return obj

    def per_article_copy(self):
        articles = self.get_articles()
        return dict([(a.pk, a.gate_copy,) for a in articles])

    def per_article_block_hash(self):
        if self.gate_type != '1':
            return {}

        articles = self.get_articles()
        return dict(flatten([a.block_to_article_hash() for a in articles]))

    def has_original_pdf(self):
        return self.original_pdf_link is not None

    def original_pdf_url(self):
        if not self.has_original_pdf():
            return ''

        return '%s?signature=%s&policy=%s' % (
            self.original_pdf_link,
            FILEPICKER_READ_SIGNATURE,
            FILEPICKER_READ_POLICY)

    def get_pdf_imports_in_progress(self):
        return self.pdfupload_set.filter(processed=False)

    def get_publication_paths(self):
        if self.pagination == 'c':
            return self.get_absolute_url()

        return [a.get_paginated_url() for a in self.get_articles()]

    def get_nav_items(self):
        return [
            {
                'name': a.name,
                'url': a.rendered_url,
                'order': a.order
            } for a in self.get_new_articles()
        ]

    def cache_json(self):
        if not self.new_style:
            return

        pub_dict = render_publication(self)
        json_dict = json.dumps(pub_dict, cls=DatetimeJSONEncoder)
        self.json = json_dict

    def upload(self):
        """
        Render and upload a new-style publication to s3.  Only html files are
        produced and uploaded.

        Alias the first article in the publication to `index.html`
        """

        if not self.new_style:
            return

        Meter('publication.upload').inc()

        with Timer('publication.upload-time'):

            articles = self.articles().all().order_by('order')
            first_article_filename = "{}/{}/index.html".format(
                self.group.slug, self.slug)

            if self.pagination == 'h':
                # Chapters

                for i, article in enumerate(articles):
                    if i == 0:
                        article.upload(filename=first_article_filename)

                    article.upload()

            elif self.pagination == 'c':
                # Continuous/scroll
                htmls = []

                for i, article in enumerate(articles):
                    obj = render_article(article)

                    if i > 0:
                        # Only show the nav for the first article
                        obj['nav'] = None

                    htmlObj = get_article_html(obj)
                    htmls.append(htmlObj)

                doc = get_scroll_publication_document(self, htmls)
                upload_article_document(first_article_filename, doc)

            else:
                pass

    @classmethod
    def create_welcome_publication(cls, group, user):
        with transaction.atomic():
            p = cls(name='Welcome to Publet', group=group, created_by=user,
                    new_style=True)
            p.save()

            data = json.loads(open('publet/projects/welcome.json').read())
            article = NewArticle(publication=p, name='Introduction', data=data,
                                 created_by=user)
            article.save()

            return p


class PublicationSlug(BaseModel):
    slug = models.SlugField(max_length=255, blank=True, unique=True)
    publication = models.ForeignKey(Publication)

    def __unicode__(self):
        return self.slug


class Preset(BaseModel):
    """
    A Preset is a default collection of blocks.  When a new Article
    within a Publication with a given Type is created, all PresetItems
    from the Preset will be added to the Article's block list.

    Publication has a Type.  A Type may have Presets.  An Article is
    created under a Publication.  An Article can only use Presets that
    belong to the Type of the Publication.

    If it sounds complicated, it is.
    """
    name = models.CharField(max_length=255)
    publication_type = models.ForeignKey(Type, null=True, blank=True)
    should_appear_in_output = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class PresetItem(models.Model):
    preset = models.ForeignKey(Preset)
    block_class_name = models.CharField(max_length=255,
                                        choices=AVAILABLE_BLOCKS_CLASSES)
    order = models.IntegerField(default=-1)

    def get_class(self):
        return globals()[self.get_block_class_name_display()]


class Article(BaseModel, BlockTypeMixin):
    """
    Articles are the root of the Publet experience, containing blocks of
    content that may be reordered, and offering the ability to render those
    ordered blocks to various outputs.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True, unique=True)
    preset = models.ForeignKey(Preset, null=True, blank=True)
    theme = models.ForeignKey(Theme, null=True, blank=True)
    publication = models.ForeignKey(Publication, blank=True)
    order = models.IntegerField(default=-1)
    uuid = UUIDField(blank=True, null=True, max_length=32, auto=True,
                     unique=True)
    domain = models.CharField(max_length=255, null=True, blank=True)
    hosted_password = models.CharField(max_length=255, null=True, blank=True)
    is_toc = models.BooleanField(default=False)
    gate_copy = models.TextField(blank=True, null=True)

    is_draft = models.BooleanField(default=False)
    parent = models.ForeignKey('self', null=True, blank=True)

    always_save = True

    class Meta:
        ordering = ['order']

    def __unicode__(self):
        return '<Article: {}>'.format(self.pk)

    @property
    def group(self):
        return self.publication.group

    @property
    def analytics_slug(self):
        return '/'.join([self.publication.analytics_slug, self.slug])

    def get_available_presets(self):
        publication = self.publication

        if not publication:
            return None

        return publication.preset_set.all()

    def get_absolute_url(self):
        return reverse('article-detail',
                       args=(self.group.slug,
                             self.publication.slug,
                             self.slug))

    def get_paginated_url(self):
        if self.publication.domain:
            if self.page_number == 1:
                return 'http://' + self.publication.domain + '/'
            else:
                return ('http://' + self.publication.domain + '/'
                        + str(self.page_number))

        if self.page_number == 1:
            return HOST + reverse(
                'preview-publication-html', args=(self.group.slug,
                                                  self.publication.slug))

        return HOST + reverse(
            'preview-publication-html-page',
            args=(self.group.slug, self.publication.slug, self.page_number))

    def get_protected_base_path(self):
        return '/protected/{}'.format(self.slug)

    def get_protected_pdf_path(self):
        return '{}/{}.pdf'.format(self.get_protected_base_path(), self.slug)

    def get_protected_epub_path(self):
        return '{}/{}.epub'.format(self.get_protected_base_path(), self.slug)

    def get_protected_mobi_path(self):
        return '{}/{}.mobi'.format(self.get_protected_base_path(), self.slug)

    def get_protected_zip_path(self):
        return '{}/{}.zip'.format(self.get_protected_base_path(), self.slug)

    def get_protected_path(self, ext):
        if ext.startswith('.'):
            ext = ext[1:]

        if ext not in ['pdf', 'zip', 'epub', 'mobi']:
            return

        method = getattr(self, 'get_protected_{}_path'.format(ext))

        if not method:
            raise Exception("Unable to get protected path for {} "
                            "extension".format(ext))

        return method()

    def get_fonts(self):
        tbs = TextBlock.objects.filter(article=self, font__isnull=False)
        return [t.font for t in tbs]

    def get_blocks(self):
        blocks = [block
                  for BlockClass in self._block_types().values()
                  for block in BlockClass.objects.filter(article=self)]
        blocks.sort(key=attrgetter('order'))

        for b in blocks:
            b.resolve()

        return blocks

    def get_render_dir(self):
        renders_dir = os.path.join(BASE_PATH, 'renders')
        article_dir = '{}/{}'.format(renders_dir, self.slug)

        if not os.path.exists(article_dir):
            os.makedirs(article_dir)

        return article_dir

    def get_css_template(self):
        return '{}/css/outputs/{}/{}/style.css'.format(
            settings.STATIC_ROOT,
            slugify(self.publication.type.name),
            slugify(self.theme.name))

    def get_mobile_css_template(self):
        return '{}/css/outputs/mobile/style.css'.format(
            settings.STATIC_ROOT,
            slugify(self.type.name),
            slugify(self.theme.name))

    def get_html_template(self):
        return 'outputs/article.html'

    def get_mobile_html_template(self):
        return 'outputs/mobile.html'

    def _render_css(self):

        css_dir = '{}/html/css'.format(self.get_render_dir())

        if not os.path.exists(css_dir):
            os.makedirs(css_dir)

        with open(self.get_css_template(), 'r') as css_file:
            rendered_css = css_file.read()

        with open('{}/style.css'.format(css_dir), 'w+') as css:
            css.write(rendered_css)

        with open('{}/base.css'.format(css_dir), 'w+') as base_css:
            with open('{}/css/skeleton/base.css'.format(settings.STATIC_ROOT),
                      'r') as css_file:
                base_css.write(css_file.read())

        with open('{}/skeleton.css'.format(css_dir), 'w+') as base_css:
            with open('{}/css/skeleton-pdf.css'.format(STATIC_ROOT),
                      'r') as css_file:
                base_css.write(css_file.read())

        with open('{}/layout.css'.format(css_dir), 'w+') as base_css:
            with open('{}/css/skeleton/layout.css'.format(STATIC_ROOT),
                      'r') as css_file:
                base_css.write(css_file.read())

        with open('{}/tomorrow.css'.format(css_dir), 'w+') as base_css:
            with open('{}/components/highlightjs/styles/tomorrow.css'.format(
                    STATIC_ROOT), 'r') as css_file:
                base_css.write(css_file.read())

    def _render_js(self):

        js_dir = '{}/html/js'.format(self.get_render_dir())

        if not os.path.exists(js_dir):
            os.makedirs(js_dir)

        with open('{}/highlight.js'.format(js_dir), 'w+') as base_js:
            with open('{}/components/highlightjs/highlight.pack.js'.format(
                    STATIC_ROOT), 'r') as js_file:
                base_js.write(js_file.read())

    def _render_html(self):

        html_dir = '{}/html'.format(self.get_render_dir())

        if not os.path.exists(html_dir):
            os.makedirs(html_dir)

        rendered_html = render_to_string(self.get_html_template(), {
            'article': self,
            'blocks': self.get_blocks()
        })

        with open('{}/index.html'.format(html_dir), 'w+') as html:
            html.write(rendered_html.encode('utf-8'))

    def _render_mobile_html_and_css(self):

        html_dir = '{}/mobile-html'.format(self.get_render_dir())

        if not os.path.exists(html_dir):
            os.makedirs(html_dir)

        css_dir = '{}/mobile-html/css'.format(self.get_render_dir())

        if not os.path.exists(css_dir):
            os.makedirs(css_dir)

        with open(self.get_mobile_css_template(), 'r') as css_file:
            rendered_css = css_file.read()

        with open('{}/style.css'.format(css_dir), 'w+') as css:
            css.write(rendered_css)

        rendered_html = render_to_string(self.get_mobile_html_template(), {
            'article': self
        })

        with open('{}/index.html'.format(html_dir), 'w+') as html:
            html.write(rendered_html.encode('utf-8'))

    def _render_html_zip(self):
        html_dir = '{}/html'.format(self.get_render_dir())
        path = self.filename_for_format('zip')

        zip_file = zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED)

        rootlen = len(html_dir) + 1
        for base, dirs, files in os.walk(html_dir):
            for file in files:
                fn = os.path.join(base, file)
                zip_file.write(fn, fn[rootlen:])

        zip_file.close()

    def render_html_zip(self):
        return tasks.generate_html_zip.delay(self)

    def _render_epub(self):
        cmd = 'sudo {} {}/mobile-html/index.html {} --no-default-epub-cover'
        cmd = cmd.format(
            settings.EPUB_GENERATION_BIN,
            self.get_render_dir(),
            self.filename_for_format('epub'))

        code = ext_call(cmd, shell=True)

        logger.info('epub render - article: {} - return: {}'.format(
            self.pk, code))

        return code

    def render_epub(self):
        return tasks.generate_epub.delay(self)

    def _render_mobi(self):
        code = ext_call('sudo {} {}/mobile-html/index.html {}/{}.mobi'.format(
            settings.EPUB_GENERATION_BIN,
            self.get_render_dir(),
            self.filename_for_format('mobi')), shell=True)

        logger.info('mobi render - article: {} - return: {}'.format(
            self.pk, code))

        return code

    def render_mobi(self):
        return tasks.generate_mobi.delay(self)

    def _render_pdf(self):
        code = ext_call(
            'sudo {} --print-media-type {}/html/index.html {}'.format(
                PDF_GENERATION_BIN,
                self.get_render_dir(),
                self.filename_for_format('pdf')), shell=True)

        logger.info('pdf render - article: {} - return: {}'.format(
            self.pk, code))

        return code

    def render_pdf(self):
        return tasks.generate_pdf.delay(self)

    def render_ext(self, ext):
        if ext == 'zip':
            ext = 'html_zip'

        method = getattr(self, 'render_{}'.format(ext))
        return method()

    def should_rerender(self, file_format):
        filename = self.filename_for_format(file_format)
        return not os.path.exists(filename)

    def filename_for_format(self, file_format):
        return os.path.join(self.get_render_dir(),
                            self.base_filename_for_format(file_format))

    def base_filename_for_format(self, file_format):
        last_modified = self.modified.strftime('%Y%m%d-%H%M%S')
        return '%s-%s.%s' % (self.slug, last_modified, file_format)

    def get_protected_file_url(self, ext):
        base_filename = self.base_filename_for_format(ext)
        return reverse('protected-article-file',
                       kwargs=dict(article_slug=base_filename))

    @property
    def page_number(self):
        return self.order + 1

    def create_preset_blocks(self):
        preset = self.preset

        if not preset:
            return None

        preset_items = preset.presetitem_set.all().order_by('order')

        for item in preset_items:
            Class = item.get_class()
            Class.objects.create(article=self, order=item.order)

    def reorder(self, block_type_ids):
        """
        Reorder all of the blocks in an article given a list of
        `[block_type, block_id]`, return the new ordering as
        `{type: {id: order}}`.
        """
        order_iter = count()
        block_types = self._block_types()
        block_ordering = dict((block_type, {}) for block_type in block_types)
        for block_type, block_id in block_type_ids:
            block_ordering[block_type][block_id] = next(order_iter)
        with transaction.atomic():
            for block_type, BlockClass in block_types.items():
                ordering = block_ordering[block_type]
                for block in BlockClass.objects.filter(article=self):
                    try:
                        order = ordering[block.id]
                    except KeyError:
                        order = next(order_iter)
                        ordering[block.id] = order
                    if block.order != order:
                        block.order = order
                        block.save(update_fields=['order'])
            self.save()  # To force updating of `modified` field
        return block_ordering

    def duplicate(self, publication=None):
        new_kwargs = []

        ignore = ['id', 'uuid', 'slug', 'modified', 'created']

        for field in self._meta.fields:
            if field.name in ignore:
                continue

            new_kwargs.append((field.name, getattr(self, field.name)))

        kwargs = dict(new_kwargs)
        kwargs['publication'] = publication

        new_article = self.__class__.objects.create(**kwargs)

        for block in self.get_blocks():
            block.duplicate(article=new_article)

        return new_article

    @property
    def simple_json(self):
        return json.dumps(dict(pk=self.pk, slug=self.slug))

    def create_draft(self):
        """
        Create a new draft article based on this one, return the new
        instance.
        """
        if self.is_draft:
            raise Exception("Can't create draft from draft.  "
                            "That would be draftception.")

        article = self.duplicate(publication=self.publication)
        article.is_draft = True
        article.order = self.order
        article.parent = self
        article.save()
        return article

    def has_draft(self):
        if self.is_draft or self.parent:
            return False

        return self.article_set.exists()

    def get_draft(self):
        if self.has_draft():
            return self.article_set.all()[0]

    def block_to_article_hash(self):
        return [(b.pk, self.pk,) for b in self.get_blocks()]

    def save(self, *args, **kwargs):

        if not self.slug:
            self.slug = slugify_uniquely(self.name, Article)

        if not self.publication:
            raise Exception('Cannot save article without publication set.')

        if not self.theme:
            self.theme = self.publication.theme

        if not self.pk:
            article_count = self.publication.get_articles().count()
            self.order = article_count

            # If this is a new instance, add preset items
            with transaction.atomic():
                instance = super(Article, self).save(*args, **kwargs)
                self.create_preset_blocks()
        else:
            instance = super(Article, self).save(*args, **kwargs)

        self.publication.invalidate_html_cache()
        return instance


# Content blocks

class DirtyMixin(object):
    # See what I did there?

    def apply(self, data):
        """
        Apply the data to the instance while preserving the old values
        in double-underscored attributes right on the instance.  We will
        use this information in ``is_dirty``.

        Currently we skip over FKs.
        """

        # TODO: API resources *cannot* have fields that have names different
        # from the model fields they represent.

        for field in self._meta.fields:
            new_value = data.get(field.name, None)

            if isinstance(field, models.ForeignKey):

                with no_queries_allowed():
                    if new_value:
                        match = resolve(new_value)
                        resource_pk = int(match.kwargs.get('pk'))
                    else:
                        resource_pk = None

                    old_value = getattr(self, '{}_id'.format(field.name))

                    setattr(self, '{}_id'.format(field.name), resource_pk)
                    setattr(self, '__{}_id'.format(field.name), old_value)

                continue

            if field.name in ['id', 'created', 'modified']:
                continue

            if field.name == 'crop_marks' and new_value is None:
                new_value = '{}'

            if field.name in ['alignment', 'text_alignment', 'line_height'] \
                    and new_value is None:
                new_value = ''

            setattr(self, '__{}'.format(field.name), getattr(self, field.name))
            setattr(self, field.name, new_value)

    def is_dirty(self):
        dirty_fields = []

        for field in self._meta.fields:
            if field.name in ['id', 'created', 'modified']:
                continue

            if isinstance(field, models.ForeignKey):
                fn = '{}_id'.format(field.name)
            else:
                fn = field.name

            old_fn = '__{}'.format(fn)

            if not hasattr(self, old_fn):
                raise Exception('Call apply first; missing {}'.format(old_fn))

            new_value = getattr(self, fn)
            old_value = getattr(self, old_fn)

            if new_value != old_value:
                dirty_fields.append(fn)

        return len(dirty_fields) > 0, dirty_fields


class StyleBase(models.Model):
    """
    This mixin gives the model all the different styling options
    """
    size = models.PositiveIntegerField(blank=True, null=True)
    line_height = models.CharField(max_length=10, blank=True)

    meta = models.CharField(max_length=1000, blank=True)

    font = models.ForeignKey(Font, blank=True, null=True)
    color = models.ForeignKey('Color', blank=True, null=True,
                              on_delete=models.SET_NULL)

    custom_css_classes = models.CharField(max_length=255, blank=True)

    alignment = models.CharField(max_length=1, choices=ALIGNMENT_CHOICES,
                                 blank=True)
    text_alignment = models.CharField(max_length=1,
                                      choices=TEXT_ALIGNMENT_CHOICES,
                                      blank=True)

    class Meta:
        abstract = True


class Flavor(BaseModel, StyleBase):
    name = models.CharField(max_length=255)
    theme = models.ForeignKey(Theme)
    type = models.CharField(max_length=5, choices=FLAVOR_TYPES)
    background_color = models.ForeignKey('Color', blank=True, null=True,
                                         related_name='background_color',
                                         on_delete=models.SET_NULL)

    def __unicode__(self):
        return '{} [{}] for {}'.format(self.name, self.get_type_display(),
                                       self.theme.name)

    @classmethod
    def create_block_defaults(cls, theme):
        font = theme.fonts.get(name='Open Sans:300,400,700')
        color = theme.get_colors().get(hex='000000')

        # Text block
        Flavor.objects.create(name='Default', type='text', theme=theme,
                              size=18, font=font, color=color, alignment='0',
                              text_alignment='l', line_height='1.4')

        # Photo block
        Flavor.objects.create(name='Default', type='photo', theme=theme,
                              size=18, font=font, color=color, alignment='0',
                              text_alignment='l', line_height='1.4')

        # Audio block
        Flavor.objects.create(name='Default', type='audio', theme=theme,
                              size=18, font=font, color=color, alignment='0',
                              text_alignment='l', line_height='1.4')

        # Video block
        Flavor.objects.create(name='Default', type='video', theme=theme,
                              size=18, font=font, color=color, alignment='0',
                              text_alignment='l', line_height='1.4')

    @classmethod
    def create_default_body(cls, theme):
        font = theme.fonts.get(name='Open Sans:300,400,700')
        color = theme.get_colors().get(hex='000000')
        Flavor.objects.create(name='Body', theme=theme, type='text', size=18,
                              font=font, color=color, text_alignment='l',
                              alignment='0', line_height='1.4')

    @classmethod
    def create_default_header(cls, theme):
        font = theme.fonts.get(name='Open Sans:300,400,700')
        color = theme.get_colors().get(hex='000000')
        Flavor.objects.create(name='Header', theme=theme, type='text', size=32,
                              text_alignment='l', font=font, color=color,
                              alignment='0')

    @classmethod
    def create_default_sub_header(cls, theme):
        font = theme.fonts.get(name='Open Sans:300,400,700')
        color = theme.get_colors().get(hex='000000')
        Flavor.objects.create(name='Sub header', theme=theme, type='text',
                              size=24, font=font, color=color,
                              text_alignment='l', alignment='0')

    def delete(self, *args, **kwargs):
        raise Exception("Flavors can't be deleted at the moment")

    def save(self, *args, **kwargs):
        super(Flavor, self).save(*args, **kwargs)
        self.theme.invalidate_html_cache_for_publications()


class BaseBlockManager(models.Manager):

    def create(self, *args, **kwargs):
        obj = self.model(**kwargs)

        if 'flavor' not in kwargs:
            obj.flavor = obj.get_default_flavor()

        obj.save(force_insert=True, using=self.db)
        return obj


class BaseBlock(BaseModel, StyleBase, DirtyMixin):
    order = models.IntegerField(default=-1)
    article = models.ForeignKey(Article, null=True, blank=True)
    flavor = models.ForeignKey(Flavor)
    is_locked = models.BooleanField(default=False)
    shareable = models.BooleanField(default=False)

    objects = BaseBlockManager()

    class Meta:
        abstract = True

    def get_article(self):
        return self.article or self.new_article

    def get_default_flavor(self):
        t = self.type

        if t == 'gallery':
            t = 'photo'

        if self.theme:
            return self.theme.flavor_set.get(name='Default', type=t)

    def duplicate(self, article=None, related=None):
        new_kwargs = []

        ignore = ['id', 'modified', 'created']

        for field in self._meta.fields:
            if field.name in ignore:
                continue

            new_kwargs.append((field.name, getattr(self, field.name)))

        kwargs = dict(new_kwargs)
        kwargs['article'] = article

        new_block = self.__class__.objects.create(**kwargs)

        if related:
            for obj in related:
                obj.duplicate(parent=new_block)

        return new_block

    @property
    def alignment_css_class(self):
        if self.type == 'gallery':

            if self.alignment == '3':
                return 'align-breaking-left-photo'

            if self.alignment == '4':
                return 'align-breaking-right-photo'

        return 'align-' + slugify(self.get_alignment_display())

    @property
    def font_class(self):
        if not self.font:
            return ""

        return 'theme-font-{}'.format(self.font.slug)

    def resolve(self):
        merged = merge(self.flavor.as_dict(), self.as_dict())

        for k, v in merged.items():
            try:
                setattr(self, k, v)
            except AttributeError:
                pass

        def ex(*args, **kwargs):
            raise AttributeError('Saving a resolved instance is illegal')

        self.save = ex

    def get_style_expressions(self):
        css = []

        if self.size is not None:
            css.append('font-size: {}px;'.format(self.size))

        if self.line_height:
            css.append('line-height: {}em;'.format(self.line_height))

        if self.text_alignment:
            css.append('text-align: {};'.format(
                self.get_text_alignment_display()))

        if self.font:
            css.append(self.font.css)

        if self.color:
            css.append('color: #{};'.format(self.color.hex))

        return css

    @property
    def style(self):
        css = self.get_style_expressions()
        return ' '.join(css)

    @property
    def is_full_align(self):
        return self.alignment == '1'

    @property
    def block_attr(self):
        """
        For use as an Angular directive
        """
        return "block='{\"alignment\": \"%s\"}' id='block-%s'" % (
            self.alignment, self.pk)

    def get_social_link(self):
        publication = self.article.publication

        if publication.embed_parent_page:
            url = publication.get_share_url()

            if publication.pagination == 'h':
                url += str(self.article.page_number)

            url += ('#block-' + str(self.pk))

            return url

        args = (
            self.type[0],
            decode(self.pk)
        )
        return 'http://' + SHORT_HOST + reverse('ultra-short-link', args=args)

    @property
    def link_to_block(self):
        article = self.article
        publication = article.publication

        args = (publication.group.slug, publication.slug,)

        url = HOST + reverse('preview-publication-html', args=args)

        if publication.pagination == 'h' and article.page_number is not 1:
            url += str(article.page_number)

        url += ('#block-' + str(self.pk))

        return url

    def submit_to_integration(self, integration):
        """
        Submit to a third-party social media service.  Like buffer.
        """
        submit_to_integration.delay(integration.pk, self.type, self.pk)

    @property
    def theme(self):
        if self.article and self.article.theme:
            return self.article.theme

    def json(self):
        return {
            'id': self.pk,
            'type': self.client_type,
            'content': self.get_json_content(),
            'classes': [],
            'created': self.created,
            'modified': self.modified
        }

    def save(self, *args, **kwargs):

        if not self.theme:
            return super(BaseBlock, self).save(*args, **kwargs)

        if not self.flavor:
            self.flavor = self.get_default_flavor()

        super(BaseBlock, self).save(*args, **kwargs)
        self.get_article().publication.invalidate_html_cache()


class CropMixin(object):

    def get_crop_marks(self):
        if not self.crop_marks:
            return None

        return json.loads(self.crop_marks)

    def get_image_url(self, width=None, cropped=True):
        image = getattr(self, self.CROP_FIELD, None)

        if not image:
            return ''

        crop = self.get_crop_marks()

        if crop:
            for k, v in crop.items():
                if v is None:
                    crop = None
                    break

        if crop:

            crop = self.scale_crop_marks(crop)

            crop_args = [crop['x'],
                         crop['y'],
                         abs(crop['x2'] - crop['x']),
                         abs(crop['y'] - crop['y2'])]

            crop_args = ','.join(map(str, crop_args))
        else:
            crop_args = None

        if crop_args and cropped and not width:
            url = ("{image}/convert?crop={crop_args}"
                   "&signature={signature}&policy={policy}")

        elif crop_args and cropped and width:
            url = ("{image}/convert?crop={crop_args}&w={width}"
                   "&signature={signature}&policy={policy}")

        elif width and width < self.width:
            url = ("{image}/convert?w={width}"
                   "&signature={signature}&policy={policy}")
        elif width and not self.width:
            url = ("{image}/convert?w={width}"
                   "&signature={signature}&policy={policy}")

        else:
            url = "{image}?signature={signature}&policy={policy}"

        data = {
            'image': image,
            'width': width,
            'signature': FILEPICKER_READ_SIGNATURE,
            'policy': FILEPICKER_READ_POLICY,
            'crop_args': crop_args
        }
        return mark_safe(url.format(**data))

    def scale_crop_marks(self, crop):
        if 'width' not in crop:
            return crop

        if 'height' not in crop:
            return crop

        x_size = float(crop['width'])
        y_size = float(crop['height'])

        x_ratio = crop['x'] / x_size
        y_ratio = crop['y'] / y_size

        x_up = int(round(x_ratio * self.width))
        y_up = int(round(y_ratio * self.height))

        x2_ratio = crop['x2'] / x_size
        y2_ratio = crop['y2'] / y_size

        x2_up = int(round(x2_ratio * self.width))
        y2_up = int(round(y2_ratio * self.height))

        return dict(x=x_up, y=y_up, x2=x2_up, y2=y2_up)

    @property
    def cropped_image_url(self):
        alignment = None
        full_size = False
        width = 700

        if hasattr(self, 'block'):
            alignment = self.block.alignment
            full_size = self.block.full_size

        if self.size == 's':
            width = 460

        if self.size == 'm':
            width = 580

        if self.size == 'l':
            width = 700

        if alignment:
            if alignment == '1':
                width = 1200

            if alignment == '2':
                width = 960

        if full_size:
            width = None

        return self.get_image_url(width=width)


class Photo(models.Model, DirtyMixin, CropMixin, CDNMixin):
    """
    A single photo in a Gallery block
    """
    CROP_FIELD = 'image'

    PHOTO_SIZES = (
        ('s', 'Small',),   # Skeleton 8 columns
        ('m', 'Medium',),  # Skeleton 10 columns
        ('l', 'Large',),   # Skeleton 12 columns
    )

    order = models.IntegerField(default=-1)
    block = models.ForeignKey('PhotoBlock')

    image = FilePickerField()

    link = models.CharField(max_length=255, blank=True)

    heading = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True)

    heading_font = models.ForeignKey(Font, blank=True, null=True,
                                     related_name='heading_font')
    heading_size = models.PositiveIntegerField(default=18)
    heading_color = models.ForeignKey('Color', blank=True, null=True,
                                      related_name='heading_colors',
                                      on_delete=models.SET_NULL)
    heading_text_alignment = models.CharField(max_length=1,
                                              choices=TEXT_ALIGNMENT_CHOICES,
                                              default='l')

    description_font = models.ForeignKey(Font, blank=True, null=True)
    description_size = models.PositiveIntegerField(default=18)
    description_color = models.ForeignKey('Color', blank=True, null=True,
                                          related_name='colors',
                                          on_delete=models.SET_NULL)
    description_text_alignment = models.CharField(
        max_length=1, choices=TEXT_ALIGNMENT_CHOICES, default='l')

    has_shadow = models.BooleanField(default=False)
    crop_marks = models.CharField(max_length=200, blank=True)

    width = models.PositiveIntegerField(blank=True, null=True)
    height = models.PositiveIntegerField(blank=True, null=True)
    size = models.CharField(max_length=1, default='l', choices=PHOTO_SIZES)

    trigger_gate = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return 'photo {}'.format(self.pk)

    def duplicate(self, parent=None):
        new_kwargs = []

        ignore = ['id', 'modified', 'created']

        for field in self._meta.fields:
            if field.name in ignore:
                continue

            new_kwargs.append((field.name, getattr(self, field.name)))

        kwargs = dict(new_kwargs)
        kwargs['block'] = parent

        return self.__class__.objects.create(**kwargs)

    @property
    def image_url(self):
        if not self.image:
            return ''
        return '%s?signature=%s&policy=%s' % (
            self.image,
            FILEPICKER_READ_SIGNATURE,
            FILEPICKER_READ_POLICY)

    @property
    def has_caption(self):
        return (self.heading != '') or (self.description != '')

    @property
    def has_link(self):
        return self.link != ''

    @property
    def clean_link(self):
        if not self.link.startswith('http'):
            return 'http://{}'.format(self.link)

        return self.link

    @property
    def heading_style(self):
        css = []

        if self.heading_font:
            css.append(self.heading_font.css)

        if self.heading_size is not None:
            css.append('font-size: {}px;'.format(self.heading_size))

        if self.heading_text_alignment:
            css.append('text-align: {};'.format(
                self.get_heading_text_alignment_display()))

        if self.heading_color:
            css.append('color: #{};'.format(self.heading_color.hex))

        return ' '.join(css)

    @property
    def description_style(self):
        css = []

        if self.description_font:
            css.append(self.description_font.css)

        if self.description_size is not None:
            css.append('font-size: {}px;'.format(self.description_size))

        if self.description_text_alignment:
            css.append('text-align: {};'.format(
                self.get_description_text_alignment_display()))

        if self.description_color:
            css.append('color: #{};'.format(self.description_color.hex))

        return ' '.join(css)

    def json(self):
        return {
            'id': self.pk,
            'url': self.image_url,
            'caption': self.heading or None,
            'description': self.description or None,
            'width': self.width,
            'height': self.height,
            'style': None,
            'alt': None
        }

    def save(self, *args, **kwargs):
        self.ensure_cdn_links('image')

        super(Photo, self).save(*args, **kwargs)

        if not self.width or not self.height:
            tasks.get_dimensions_for_photo.delay(self.pk)


class PhotoBlock(BaseBlock):
    """
    The gallery block contains multiple gallery.
    """
    GRID_TYPES = (
        ('single', 'Single Image',),
        ('grid', 'Grid',),
        ('slideshow', 'Slideshow',),
        ('cover', 'Cover'),
    )

    grid_type = models.CharField(max_length=20, choices=GRID_TYPES,
                                 default='single')
    grid_size = models.IntegerField(default=3)
    cover_content_title = models.TextField(blank=True)
    cover_content_subtitle = models.TextField(blank=True)

    cover_font_title = models.ForeignKey(Font, blank=True, null=True,
                                         related_name='cover_font_title')
    cover_size_title = models.PositiveIntegerField(default=18)
    cover_color_title = models.ForeignKey('Color', blank=True, null=True,
                                          related_name='cover_colors_title',
                                          on_delete=models.SET_NULL)
    cover_text_alignment_title = models.CharField(
        max_length=1, choices=TEXT_ALIGNMENT_CHOICES, default='l')

    cover_font_subtitle = models.ForeignKey(Font, blank=True, null=True,
                                            related_name='cover_font_subtitle')
    cover_size_subtitle = models.PositiveIntegerField(default=18)
    cover_color_subtitle = models.ForeignKey(
        'Color', blank=True, null=True, related_name='cover_colors_subtitle')
    cover_text_alignment_subtitle = models.CharField(
        max_length=1, choices=TEXT_ALIGNMENT_CHOICES, default='l')

    full_size = models.BooleanField(default=False)

    caption = models.TextField(blank=True)

    def __unicode__(self):
        return 'gallery {}'.format(self.pk)

    @property
    def style_cover_title(self):
        css = ['font-size: {}px;'.format(self.cover_size_title),
               'line-height: {}em;'.format(self.line_height)]

        if self.cover_font_title:
            css.append(self.cover_font_title.css)

        css.reverse()
        return ' '.join(css)

    @property
    def style_cover_subtitle(self):
        css = ['font-size: {}px;'.format(self.cover_size_subtitle),
               'line-height: {}em;'.format(self.line_height)]

        if self.cover_font_subtitle:
            css.append(self.cover_font_subtitle.css)

        css.reverse()
        return ' '.join(css)

    @property
    def type(self):
        return 'gallery'

    @property
    def client_type(self):
        return 'ImageBlock'

    def ordered_photos(self):
        return self.photo_set.all().order_by('order')

    def duplicate(self, article=None):
        related = self.photo_set.all()
        return super(PhotoBlock, self).duplicate(article=article,
                                                 related=related)

    @property
    def has_cover_content_title(self):
        return self.cover_content_title != ''

    @property
    def has_cover_content_subtitle(self):
        return self.cover_content_subtitle != ''

    def get_json_content(self):
        try:
            return self.ordered_photos()[0].json()
        except IndexError:
            return []


class TextBlock(BaseBlock):
    """
    This is a simple block of text.
    """
    content = models.TextField(default=' ')

    # Overrides
    list_style = models.CharField(max_length=20, default='disc',
                                  choices=LIST_STYLE_TYPE_OPTIONS)
    is_bullets = models.BooleanField(default=False)
    is_embed = models.BooleanField(default=False)
    is_indented = models.BooleanField(default=False)

    background_color = models.ForeignKey('Color', blank=True, null=True,
                                         related_name='text_background_color',
                                         on_delete=models.SET_NULL)

    @property
    def type(self):
        return 'text'

    @property
    def client_type(self):
        return 'TextBlock'

    def get_style_expressions(self):
        css = super(TextBlock, self).get_style_expressions()

        if self.is_indented:
            css.append('margin-left: 1.5em;')
            css.append('margin-right: 1.5em;')

        if self.background_color:
            css.append('background-color: #{};'.format(
                self.background_color.hex))

        return css

    def get_lines(self):
        undiv = self.processed_html.replace('</div>', '')
        return undiv.split('<div>')

    @property
    def processed_html(self):
        # Adding the blank target breaks all the things.
        # return self.content.replace('<a href', '<a target="_blank" href')
        return self.content

    def as_plain_text(self):
        return clean(self.content, tags=[], strip=True).strip()

    @property
    def es_mapping(self):
        return {
            "mappings": {
                "block": {
                    "properties": {
                        "block_id": {
                            "type": "long"
                        },
                        "created": {
                            "type": "date",
                            "format": "dateOptionalTime"
                        },
                        "publication_id": {
                            "type": "long"
                        },
                        "content": {
                            "type": "string",
                            "analyzer": "english"
                        },
                        "live": {
                            "type": "boolean"
                        },
                        "group_id": {
                            "type": "long"
                        },
                        "article_id": {
                            "type": "long"
                        },
                        "id": {
                            "type": "long"
                        }
                    }
                }
            }
        }

    def es_doc(self):
        return {
            'content': strip_tags(self.content),
            'block_id': self.pk,
            'article_id': self.article.pk,
            'publication_id': self.article.publication.pk,
            'group_id': self.article.publication.group.pk
        }

    def get_json_content(self):
        return {
            'text': self.content,
            'style': None
        }

    def save(self, *args, **kwargs):
        super(TextBlock, self).save(*args, **kwargs)
        tasks.index_text_block.delay(self.pk)


class VideoBlock(BaseBlock, CropMixin, CDNMixin):
    """
    The video block should accept multiple video embed URLs, TBD.
    """
    CROP_FIELD = 'preview'
    VIMEO_REGEX = re.compile(r'https?://([^/]+\.)?vimeo.com'
                             '/(channels/[\w]+[#|/])?(?P<video_id>\d+)')
    YOUTUBE_HOSTNAMES = ('youtu.be', 'youtube.com',  'www.youtube.com',)
    YOUTUBE_URL_PATTERNS = [re.compile(x) for x in [
        r'youtube.com/.*?v[/=](?P<video_id>[\w-]+)',
        r'youtu.be/(?P<video_id>[\w-]+)',
    ]]

    video_url = models.CharField(max_length=255)

    width = models.PositiveIntegerField(blank=True, null=True)
    height = models.PositiveIntegerField(blank=True, null=True)

    preview = models.CharField(max_length=255, blank=True)
    crop_marks = models.CharField(max_length=200, blank=True)

    caption = models.TextField(blank=True)

    @property
    def type(self):
        return 'video'

    @property
    def client_type(self):
        return 'VideoBlock'

    @property
    def preview_url(self):
        if not self.preview:
            return ''
        return '%s?signature=%s&policy=%s' % (
            self.preview,
            FILEPICKER_READ_SIGNATURE,
            FILEPICKER_READ_POLICY)

    @property
    def small_thumb(self):
        if not self.preview:
            return ''

        return '{}/convert?w={}&signature={}&policy={}'.format(
            self.preview, 500, FILEPICKER_READ_SIGNATURE,
            FILEPICKER_READ_POLICY)

    @property
    def big_thumb(self):
        if not self.preview:
            return ''

        return '{}/convert?w={}&signature={}&policy={}'.format(
            self.preview, 1000, FILEPICKER_READ_SIGNATURE,
            FILEPICKER_READ_POLICY)

    @property
    def video_type(self):
        if self.VIMEO_REGEX.match(self.video_url):
            return 'vimeo'

        hostname = urlparse(self.video_url).netloc

        if hostname in self.YOUTUBE_HOSTNAMES:
            return 'youtube'

    @property
    def is_youtube(self):
        return self.video_type == 'youtube'

    @property
    def is_vimeo(self):
        return self.video_type == 'vimeo'

    @property
    def video_id(self):
        if self.video_type == 'youtube':
            return self._get_youtube_id()
        elif self.video_type == 'vimeo':
            return self._get_vimeo_id()
        else:
            return None

    def _get_youtube_id(self):
        for pattern in self.YOUTUBE_URL_PATTERNS:
            match = pattern.search(self.video_url)
            video_id = match and match.group('video_id')

            if bool(video_id):
                return video_id

    def _get_vimeo_id(self):
        return self.VIMEO_REGEX.match(self.video_url).groupdict().get(
            'video_id')

    def populate_vimeo_metadata(self):
        url = 'http://vimeo.com/api/v2/video/{}.json'.format(self.video_id)
        r = requests.get(url)

        if r.status_code > 399:
            return

        try:
            meta = r.json()[0]

            self.preview = meta['thumbnail_large']
            self.width = meta['width']
            self.height = meta['height']
            self.save()

        except (KeyError, IndexError):
            return

    @property
    def ratio(self):
        if self.width and self.height:
            return round(float(self.width) / float(self.height), 2)

    @property
    def has_preview(self):
        return self.preview or self.is_youtube or self.is_vimeo

    @property
    def has_caption(self):
        return self.caption != ''

    def save(self, *args, **kwargs):
        self.ensure_cdn_links('preview')

        super(VideoBlock, self).save(*args, **kwargs)

        if self.is_vimeo:
            if not self.width or not self.height:
                tasks.get_vimeo_metadata.delay(self.pk)


class AudioBlock(BaseBlock):
    """
    The audio block should accept multiple audio embed URLs, TBD.
    """
    audio_url = models.CharField(max_length=255)
    label = models.CharField(max_length=255, blank=True)

    @property
    def type(self):
        return 'audio'

    @property
    def has_caption(self):
        return self.label != ''


# Content models

class Asset(BaseModel, DirtyMixin, CDNMixin):
    block = models.ForeignKey(TextBlock)
    filename = models.CharField(max_length=255, blank=True)
    label = models.CharField(max_length=255, blank=True)

    def duplicate(self, parent=None):
        new_kwargs = []

        ignore = ['id', 'modified', 'created']

        for field in self._meta.fields:
            if field.name in ignore:
                continue

            new_kwargs.append((field.name, getattr(self, field.name)))

        kwargs = dict(new_kwargs)
        kwargs['block'] = parent

        return self.__class__.objects.create(**kwargs)

    @property
    def asset_url(self):
        if not self.filename:
            return ''
        return '%s?signature=%s&policy=%s' % (
            self.filename,
            FILEPICKER_READ_SIGNATURE,
            FILEPICKER_READ_POLICY)

    def save(self, *args, **kwargs):
        self.ensure_cdn_links('filename')

        super(Asset, self).save(*args, **kwargs)


class Color(BaseModel):
    hex = models.CharField(max_length=10)
    theme = models.ForeignKey(Theme, null=True)

    def __unicode__(self):
        return self.hex

    @classmethod
    def create_default_colors(cls, theme):
        objs = []

        colors = [
            '000000',  # black
            'ffffff',  # white
            '9D3434',  # mellow red
            '21635A',  # old green
            '333333',  # gray
            '919191',  # light gray
            '1C4382',  # warm blue
            'D59439'   # punchy yellow
        ]

        for c in colors:
            objs.append(cls(hex=c, theme=theme))

        return cls.objects.bulk_create(objs)

    def save(self, *args, **kwargs):
        if self.hex.startswith('#'):
            self.hex = self.hex[1:]
        super(Color, self).save(*args, **kwargs)

    def detect_cascading_queries(self):
        related = self._meta.get_all_related_objects()

        for obj in related:
            query = {
                obj.field.name: self
            }

            refs = obj.model.objects.filter(**query)

            if refs:
                raise Exception("This will cause a cascading delete.")


# Pipelines

def change_publication_group(publication, group):
    """
    If you'd like to update a publication's group, this is the *only*
    way to do it.  Don't go changing it directly.
    """

    # NOTE: This is here for historical reasons because the previous version of
    # the data model included a `group` field on Article instances.
    with transaction.atomic():
        publication.group = group
        publication.save()


# Misc

class Readability(BaseModel):
    COMMON_DOMAINS = {
        'techcrunch.com': 'TechCrunch',
        'www.nytimes.com': 'The New York Times',
        'www.slate.com': 'Slate',
        'online.wsj.com': 'The Wall Street Journal'
    }

    url = models.CharField(max_length=255)
    is_processed = models.BooleanField(default=False)

    article = models.ForeignKey(Article, null=True, blank=True)
    publication = models.ForeignKey(Publication)

    def __unicode__(self):
        return self.url

    def get_or_create_toc_for_publication(self, publication):
        # Note that a normal get_or_create won't work here because this
        # code runs in a db transaction --- lame
        try:
            return Article.objects.get(publication=publication,
                                       name=TOC_ARTICLE_NAME,
                                       is_toc=True)
        except Article.DoesNotExist:
            return Article.objects.create(publication=publication,
                                          name=TOC_ARTICLE_NAME,
                                          is_toc=True, order=0)

    def get_source_for_url(self, url):
        """
        Try and see if the domain is one of the common ones;  if not,
        just return the hostname.
        """
        source = urlparse(self.url).hostname
        return self.COMMON_DOMAINS.get(source, source)

    def get_leading_sentences(self, text, num=3):
        text = text.replace('\n', ' ')
        text = text.replace('   ', ' ')
        text = text.replace('  ', ' ')
        sentences = text.split('. ')[:num]
        return ' '.join(map(lambda x: x + '.', sentences))

    def format_date(self, date):
        year, month, day = date['year'], date['month'], date['day']

        if month.startswith('0'):
            month = month[1:]

        if day.startswith('0'):
            day = day[1:]

        year = int(year)
        month = int(month)
        day = int(day)

        if month > 12 and day <= 12:
            month, day = day, month

        date_f = '%B %-d, %Y'
        return datetime.date(year, month, day).strftime(date_f)

    def create_toc_entry(self, doc):
        toc = self.get_or_create_toc_for_publication(self.publication)

        blocks = toc.get_blocks()
        blocks.reverse()

        if not blocks:
            next_block_order = -1
        else:
            next_block_order = blocks[0].order + 1

        source = self.get_source_for_url(self.url)
        summary = self.get_leading_sentences(' '.join(doc['paragraphs']))

        date = ''

        if doc['dates']:
            date = self.format_date(doc['dates'][0])

        content = render_to_string('toc-entry.html', {
            'url': self.url,
            'title': doc['title'],
            'source': source,
            'summary': summary,
            'date': date
        })

        TextBlock.objects.create(article=toc, content=content,
                                 order=next_block_order)

    def parse(self, html):
        if self.is_processed:
            return

        doc = parse.parse_html(html)

        with transaction.atomic():
            existing_article_count = self.publication.article_set.count()
            article = Article.objects.create(name=doc['title'],
                                             publication=self.publication,
                                             group=self.publication.group,
                                             order=existing_article_count + 1)

            TextBlock.objects.create(article=article, content=doc['title'],
                                     size=24, order=-1)
            TextBlock.objects.create(article=article, content=self.url,
                                     order=0)

            counter = 1

            if doc['dates']:
                date = '{year}-{month}-{day}'.format(**doc['dates'][0])
                TextBlock.objects.create(article=article, content=date)
                counter += 1

            for p in doc['paragraphs']:
                p += '\n\n'
                TextBlock.objects.create(article=article, content=p,
                                         order=counter)
                counter += 1

            self.is_processed = True
            self.save()

            self.create_toc_entry(doc)


EVENT_TYPES = (
    (1, 'Article added',),
    (2, 'Article removed',),

    (3, 'Text block added',),
    (4, 'Photo block added',),
    (5, 'Audio block added',),
    (6, 'Video block added',),

    (7, 'Text block removed',),
    (8, 'Photo block removed',),
    (9, 'Audio block removed',),
    (10, 'Video block removed',),
)


class EventManager(models.Manager):

    def for_article(self, article):
        return self.filter(parent_article=article).order_by('-created')[:100]

    def for_publication(self, publication):
        return self.filter(
            Q(parent_article__publication=publication) |
            Q(parent_publication=publication)).order_by('-created')[:100]


class Event(BaseModel):
    type = models.PositiveIntegerField(choices=EVENT_TYPES)
    parent_article = models.ForeignKey(Article, null=True, blank=True)
    parent_publication = models.ForeignKey(Publication, null=True, blank=True)

    objects = EventManager()

    def __unicode__(self):
        return self.get_type_display()

    @property
    def is_article_edit(self):
        return self.parent_publication is None

    @property
    def is_publication_edit(self):
        return self.parent_article is None


class PublicationSocialGateEntryManager(models.Manager):

    def per_block(self, publication, days=30):
        query = """
        select block_id,block_type,referrer,count(*)
                            from projects_publicationsocialgateentry
          where
              publication_id = %s
              and created > 'now'::date - '%s days'::interval
            group by block_id, block_type, referrer
            order by block_id;
        """
        with Timer('sql.social-gate-per-block'):
            cursor = connection.cursor()
            cursor.execute(query, [publication.id, days])
            rows = cursor.fetchall()

        result = []

        for block_id, block_values in groupby(rows, key=lambda x: x[0]):
            clean = []

            for _, type, referrer, num in block_values:
                clean.append((referrer, num,))

            obj = {
                'values': dict(clean),
                'id': block_id,
                'type': type
            }

            result.append((block_id, obj,))

        return dict(result)

    def conversion_count(self, publication, days=30):
        query = """
        select count(*) from projects_publicationsocialgateentry
            where
                publication_id = %s
                and created > 'now'::date - '%s days'::interval
        """
        with Timer('sql.social-gate-per-block'):
            cursor = connection.cursor()
            cursor.execute(query, [publication.id, days])
            rows = cursor.fetchone()

            if rows:
                rows = rows[0]

        return rows

    def for_publication(self, publication, days=30):
        kwargs = {
            'publication_id': publication
        }
        if days:
            dt = datetime.datetime.utcnow() - datetime.timedelta(days=days)
            kwargs['created__gte'] = dt

        return self.filter(**kwargs).order_by('created')

    def as_csv(self, publication, days=30):
        f = StringIO()

        writer = csv.writer(f)
        writer.writerow(['name', 'email', 'referrer', 'timestamp'])

        qs = self.for_publication(publication.id, days=days)

        for entry in qs:

            writer.writerow([
                entry.name,
                entry.email,
                entry.referrer,
                entry.created.strftime('%Y-%m-%d %H:%M:%S')
            ])

        f.seek(0)
        return f.read()

    def as_table(self, publication, days=30, conversions=None):
        if not conversions:
            conversions = self.for_publication(publication.id, days=days)

        values = []
        header = ['name', 'email', 'referrer', 'timestamp']

        for entry in conversions:
            values.append([
                entry.name,
                entry.email,
                entry.referrer,
                entry.created.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return {
            'header': header,
            'values': values
        }


class PublicationSocialGateEntry(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    publication = models.ForeignKey(Publication, blank=True, null=True)
    block_id = models.IntegerField(blank=True, null=True)
    block_type = models.CharField(max_length=10, blank=True, default='')
    email = models.EmailField()
    name = models.CharField(max_length=255, blank=True)
    referrer = models.CharField(max_length=255, blank=True)
    anonymous_id = models.CharField(max_length=255, blank=True)

    objects = PublicationSocialGateEntryManager()

    def __unicode__(self):
        return self.email


class GateSubmissionManager(models.Manager):

    def for_publication(self, publication, days=30):
        kwargs = {
            'publication_id': publication
        }
        if days:
            dt = datetime.datetime.utcnow() - datetime.timedelta(days=days)
            kwargs['created__gte'] = dt

        return self.filter(**kwargs).order_by('created')

    def as_csv(self, publication, days=30):
        f = StringIO()

        writer = csv.writer(f)

        qs = self.for_publication(publication.id, days=days)

        has_header = False

        for e in qs:
            obj = e.data
            keys = obj.keys()
            keys.sort()

            if not has_header:
                header = keys + ['created']
                writer.writerow(header)
                has_header = True

            vals = map(lambda x: obj.get(x), keys)
            vals.append(e.created.strftime('%Y-%m-%d %H:%M:%S'))

            writer.writerow(vals)

        f.seek(0)
        return f.read()

    def as_table(self, publication, days=30, conversions=None):
        if not conversions:
            conversions = self.for_publication(publication.id, days=days)

        header = None
        values = []

        for e in conversions:
            obj = e.data

            if isinstance(obj, basestring):
                obj = eval(obj)

            keys = obj.keys()
            keys.sort()

            if not header:
                header = keys + ['created']

            vals = map(lambda x: obj.get(x), keys)
            vals.append(e.created.strftime('%Y-%m-%d %H:%M:%S'))
            values.append(vals)

        return {
            'header': header,
            'values': values
        }

    def conversion_count(self, publication, days=30):
        query = """
        select count(*) from projects_gatesubmission
            where
                publication_id = %s
                and created > 'now'::date - '%s days'::interval
        """
        with Timer('sql.gate-submission-count'):
            cursor = connection.cursor()
            cursor.execute(query, [publication.id, days])
            rows = cursor.fetchone()

            if rows:
                rows = rows[0]

        return rows


class GateSubmission(BaseModel):
    """
    This is a general purpose submission model.  It can be used for any client
    with any requirements because it stores the responses in a JSON field.
    This is fine because we never need to do any processing on that data; we
    simply pass it on to the customer in CSV format.
    """

    publication = models.ForeignKey(Publication)
    data = JsonField()
    anonymous_id = models.CharField(max_length=255, blank=True)

    objects = GateSubmissionManager()


class PDFUpload(BaseModel):
    """
    A PDF file on Filepicker, attached to a Publication --- intended for
    parsing into articles.
    """
    url = FilePickerField(unique=True)
    filename = models.CharField(max_length=255)
    publication = models.ForeignKey(Publication)
    processed = models.BooleanField(default=False)

    def __unicode__(self):
        return self.filename

    def get_render_dir(self):
        path = os.path.join(self.publication.get_render_dir(),
                            'pdfs',
                            str(self.pk))
        if not os.path.exists(path):
            os.makedirs(path)

        return path

    @property
    def local_path(self):
        return os.path.join(self.get_render_dir(), 'file.pdf')

    @property
    def local_xml_path(self):
        return os.path.join(self.get_render_dir(), 'file.xml')

    def download(self):
        if not self.pk:
            return

        if os.path.exists(self.local_path):
            return self.local_path

        try:
            return download_file(self.full_url, self.local_path)
        except:
            return None

    def import_to_publication(self):
        """
        Download, run pdftohtml, parse xml, import into blocks
        """
        self.download()
        self.run_pdftohtml()
        articles, default_font = self.parse()
        self.create_articles(articles, default_font)
        self.notify()

        self.processed = True
        self.save()

    def run_pdftohtml(self):
        ext_call('pdftohtml -xml -fontfullname {}'.format(self.local_path),
                 shell=True)

    def parse(self):
        if not os.path.exists(self.local_xml_path):
            return

        xml = open(self.local_xml_path).read()
        return parse_pdf_from_xml(xml)

    def get_or_create_textblock_flavor(self, font, default_font):
        # Make sure this is called in a transaction.  The create_article
        # method does that already.
        theme = self.publication.theme

        if font.font_id == default_font.font_id:
            insert = 'body '
        elif font.size > default_font.size:
            insert = 'heading '
        else:
            insert = ''

        name = 'PDF {}text style #{}'.format(insert, font.font_id)
        hex = font.color[1:]

        try:
            color = theme.color_set.filter(hex=hex)[0]
        except IndexError:
            color = Color.objects.create(hex=hex, theme=theme)

        font_parts = font.family.split('+')

        if len(font_parts) == 2:
            font_name = font_parts[1]
        elif len(font_parts) == 1:
            font_name = font_parts[0]
        else:
            font_name = 'Font'

        try:
            font_obj = theme.fonts.filter(name=font_name)[0]
        except IndexError:
            font_obj = Font.objects.create(name=font_name)
            theme.fonts.add(font_obj)

        return Flavor.objects.get_or_create(theme=theme, type='text',
                                            name=name, color=color,
                                            font=font_obj,
                                            size=int(font.size))[0]

    def get_or_create_photoblock_flavor(self):
        name = 'PDF import photo'
        theme = self.publication.theme
        return Flavor.objects.get_or_create(theme=theme, type='photo',
                                            name=name)[0]

    def create_articles(self, articles, default_font):
        for page_number, article in enumerate(articles):
            self.create_article(article, page_number, default_font)

    def create_article(self, pseudo_article, page_number, default_font):
        f = 'https://www.filepicker.io'
        cdn = 'https://cdn.publet.com'

        with transaction.atomic():
            article_name = '{} - page {}'.format(self.filename,
                                                 page_number + 1)
            article = Article.objects.create(publication=self.publication,
                                             group=self.publication.group,
                                             name=article_name,
                                             order=page_number)

            for order, block in enumerate(pseudo_article):
                if isinstance(block, PDFText):
                    content = block.text
                    font = block.font or default_font
                    flavor = self.get_or_create_textblock_flavor(
                        font, default_font)
                    TextBlock.objects.create(article=article, content=content,
                                             order=order, flavor=flavor)
                elif isinstance(block, PDFPhoto):
                    photo_path = os.path.join(self.get_render_dir(),
                                              block.filename)
                    flavor = self.get_or_create_photoblock_flavor()
                    pb = PhotoBlock.objects.create(article=article,
                                                   order=order,
                                                   flavor=flavor)
                    fp = upload_file_to_filepicker(photo_path)

                    if not fp:
                        continue

                    url = fp['url'].replace(f, cdn)
                    Photo.objects.create(block=pb, image=url)
                else:
                    pass

    @property
    def full_url(self):
        return '%s?signature=%s&policy=%s' % (
            self.url,
            FILEPICKER_READ_SIGNATURE,
            FILEPICKER_READ_POLICY)

    def notify(self):
        if not self.created_by.email:
            return

        message = render_to_string('publications/pdf-import-notification.txt',
                                   {'publication': self.publication})
        self.created_by.email_user('PDF imported!', message)

    def save(self, *args, **kwargs):
        created = False if self.pk else True
        super(PDFUpload, self).save(*args, **kwargs)

        if created:
            tasks.import_pdf_upload.delay(self.pk)


# Signal handlers

@receiver(post_save, sender=Article)
@receiver(post_save, sender=TextBlock)
@receiver(post_save, sender=PhotoBlock)
@receiver(post_save, sender=AudioBlock)
@receiver(post_save, sender=VideoBlock)
def model_saved_handler(sender, instance, created, **kwargs):
    if not created:
        return

    if sender == Article:
        Event.objects.create(type=1, created_by=instance.created_by,
                             parent_publication=instance.publication)
    else:
        parent = instance.article

        if not parent:
            parent = instance.new_article

        if parent.is_draft:
            return

        if sender == TextBlock:
            type = 3
        elif sender == PhotoBlock:
            type = 4
        elif sender == AudioBlock:
            type = 5
        elif sender == VideoBlock:
            type = 6
        else:
            type = None

        if type:
            Event.objects.create(type=type, created_by=instance.created_by,
                                 parent_article=parent)

###############################################################################
#
# New style Articles
#
###############################################################################


def article_op(op):
    return op['path'].startswith('/article')


def nav_op(op):
    return op['path'].startswith('/publication/nav')


def theme_op(op):
    return op['path'].startswith('/theme')


class NewTheme(BaseModel):
    name = models.CharField(max_length=255)
    group = models.ForeignKey(Group)
    data = JsonField(blank=True)
    id_counter = models.IntegerField(default=0)

    def __unicode__(self):
        return self.name

    @classmethod
    def create_default_theme_for_group(cls, group):
        t = cls(name='Default', group=group)
        t.save()
        return t

    @property
    def fonts_url(self):
        return HOST + reverse('api-theme-font-detail', args=(self.pk,))

    def update(self, ops):
        theme_ops = ifilter(theme_op, ops)
        theme = {
            'theme': self.data
        }
        proposed_data = jsonpatch.apply_patch(theme, theme_ops)['theme']

        if 'id' not in proposed_data:
            return

        # TODO: Ensure that themes can't be moved between groups.
        # TODO: Check permissions (maybe in resource?)
        # if proposed_data['id'] != publication_theme_id:
        #     return

        self.data = proposed_data
        self.save()

    @property
    def default_data(self):
        return {
            "buttonStyles": {
                "CTA": {
                    "name": "CTA",
                    "style": {
                        "background": "ghostwhite",
                        "borderColor": "silver",
                        "borderRadius": "2px",
                        "borderStyle": "solid",
                        "borderWidth": "1px",
                        "color": "dimgray",
                        "fontSize": "1.2rem",
                        "fontWeight": "800",
                        "letterSpacing": "2px",
                        "padding": ".75em 2em",
                        "textTransform": "uppercase"
                    }
                },
                "default": {
                    "name": "default",
                    "style": {
                        "background": "grey",
                        "borderColor": "dimgray",
                        "borderRadius": "2px",
                        "borderStyle": "solid",
                        "borderWidth": "1px",
                        "color": "lightgrey",
                        "fontSize": "1rem",
                        "fontWeight": 400,
                        "padding": ".85em 1.5em",
                        "textTransform": "capitalize"
                    }
                },
                "secondary": {
                    "name": "secondary",
                    "style": {
                        "background": "darkgrey",
                        "borderColor": "gray",
                        "borderStyle": "solid",
                        "borderWidth": "1px",
                        "padding": ".85em 1.5em",
                        "textTransform": "capitalize"
                    }
                }
            },
            "fontSizes": [
                "8px",
                "10px",
                "12px",
                "14px",
                "16px",
                "18px",
                "20px",
                "24px",
                "36px"
            ],
            "fonts": [
                {
                    "fontFamily": " \"open sans\", helvetica, sans-serif",
                    "name": "open sans",
                    "url": ''
                }
            ],
            "imageStyles": {
                "card": {
                    "name": "card",
                    "style": {
                        "background": "whitesmoke",
                        "borderColor": "silver",
                        "borderRadius": "2px",
                        "borderStyle": "solid",
                        "borderWidth": "1px",
                        "padding": ".5em"
                    }
                },
                "default": {
                    "name": "default",
                    "style": {}
                }
            },
            "palette": [
                {
                    "hex": "#1d2b54",
                    "name": "dark blue"
                },
                {
                    "hex": "#1c4382",
                    "name": "blue"
                },
                {
                    "hex": "#d59439",
                    "name": "yellow"
                },
                {
                    "hex": "#21635a",
                    "name": "dark teal"
                },
                {
                    "hex": "#b43833",
                    "name": "red"
                },
                {
                    "hex": "#9d3434",
                    "name": "dark red"
                },
                {
                    "hex": "#FFFFFF",
                    "name": "white"
                },
                {
                    "hex": "#919191",
                    "name": "grey"
                },
                {
                    "hex": "#333333",
                    "name": "dark grey"
                },
                {
                    "hex": "#000000",
                    "name": "black"
                }
            ],
            "quoteStyles": {
                "card": {
                    "name": "card",
                    "style": {
                        "background": "whitesmoke",
                        "borderColor": "silver",
                        "borderRadius": "2px",
                        "borderStyle": "solid",
                        "borderWidth": "1px",
                        "padding": ".5em"
                    }
                },
                "default": {
                    "name": "default",
                    "style": {}
                }
            },
            "textStyles": {
                "header1": {
                    "name": "header1",
                    "style": {
                        "color": "#1d2b54",
                        "fontFamily": " \"open sans\", helvetica, sans-serif",
                        "fontSize": "24px",
                        "fontWeight": "700"
                    }
                },
                "header2": {
                    "name": "header2",
                    "style": {
                        "color": "#1d2b54",
                        "fontFamily": " \"open sans\", helvetica, sans-serif",
                        "fontSize": "18px",
                        "fontWeight": "600"
                    }
                },
                "header3": {
                    "name": "header3",
                    "style": {
                        "color": "#333333",
                        "fontFamily": " \"open sans\", helvetica, sans-serif",
                        "fontSize": "18px",
                        "fontWeight": "600"
                    }
                },
                "paragraph": {
                    "name": "paragraph",
                    "style": {
                        "color": "black",
                        "fontFamily": " \"open sans\", helvetica, sans-serif",
                        "fontSize": "14px",
                        "fontWeight": "400",
                        "letterSpacing": "0px",
                        "textTransform": "none"
                    }
                },
                "subhead1": {
                    "name": "subhead1",
                    "style": {
                        "color": "#919191",
                        "fontFamily": " \"open sans\", helvetica, sans-serif",
                        "fontSize": "16px",
                        "fontWeight": "600"
                    }
                },
                "title": {
                    "name": "title",
                    "style": {
                        "color": "white",
                        "fontFamily": " \"open sans\", helvetica, sans-serif",
                        "fontSize": "36px",
                        "fontWeight": "700",
                        "textTransform": "none"
                    }
                }
            },
            "videoStyles": {
                "card": {
                    "name": "card",
                    "style": {
                        "background": "whitesmoke",
                        "borderColor": "silver",
                        "borderRadius": "2px",
                        "borderStyle": "solid",
                        "borderWidth": "1px",
                        "padding": ".5em"
                    }
                },
                "default": {
                    "name": "default",
                    "style": {}
                }
            }
        }

    def assert_ids(self):
        _id = Id(self.id_counter)

        def _fonts(font):
            if 'id' not in font:
                font['id'] = _id()
            return font

        def assert_ids(data):
            fonts = map(_fonts, data['fonts'])
            data['fonts'] = fonts
            return data

        self.data = assert_ids(self.data)
        self.id_counter = _id()

    def save(self, *args, **kwargs):
        if not self.data:
            self.data = self.default_data

        self.assert_ids()
        validate_theme(self.data)
        super(NewTheme, self).save(*args, **kwargs)

        if 'id' not in self.data:
            self.data['id'] = self.pk
            self.save()


class NewArticle(BaseModel):
    name = models.CharField(max_length=255)
    publication = models.ForeignKey(Publication)
    order = models.IntegerField(default=0)
    data = JsonField()
    id_counter = models.IntegerField(default=0)

    # Sha is used to store the hash of the rendered article
    sha = models.CharField(max_length=40, blank=True, null=True)

    def duplicate(self, publication=None):
        new_kwargs = []

        ignore = ['id', 'modified', 'created']

        for field in self._meta.fields:
            if field.name in ignore:
                continue

            new_kwargs.append((field.name, getattr(self, field.name)))

        kwargs = dict(new_kwargs)
        kwargs['publication'] = publication

        return self.__class__.objects.create(**kwargs)

    @property
    def url(self):
        return '{}/editor/#/{}'.format(
            ARTICLE_EDITOR_BASE_URL, self.pk)

    def update(self, ops):
        article_ops = ifilter(article_op, ops)
        article = {
            'article': self.data
        }
        proposed_data = jsonpatch.apply_patch(article, article_ops)['article']

        self.data = proposed_data
        self.save()

        theme = self.publication.new_theme
        theme.update(ops)

    @property
    def slug(self):
        return slugify(self.name)

    def get_filename(self):
        """
        Never called for continuous
        """
        publication = self.publication
        group = publication.group

        return "{}/{}/{}".format(group.slug, publication.slug, self.slug)

    @property
    def rendered_url(self):
        if self.publication.pagination == 'c':
            return '{}/{}/{}/#{}'.format(
                PREVIEW_URL, self.publication.group.slug,
                self.publication.slug, int_to_string(self.order))

        return '{}/{}'.format(PREVIEW_URL, self.get_filename())

    def upload(self, filename=None):
        with Timer('article.upload-time'):
            Meter('article.upload').inc()
            article = render_article(self)
            filename = filename or self.get_filename()
            html = get_article_html(article)

            doc = get_article_document(self, html)
            upload_article_document(filename, doc)

            return filename

    def assert_ids(self):
        _id = Id(self.id_counter)

        def _blocks(block):
            if 'id' not in block:
                block['id'] = _id()
            return block

        def _columns(column):
            return map(_blocks, column)

        def _sections(section):
            if 'id' not in section:
                section['id'] = _id()

            columns = map(_columns, section['columns'])
            section['columns'] = columns
            return section

        def assert_ids(data):
            sections = map(_sections, data['sections'])
            data['sections'] = sections
            return data

        self.data = assert_ids(self.data)
        self.id_counter = _id()

    def save(self, *args, **kwargs):
        created = False if self.pk else True

        if not self.created_by:
            raise CreatedByBlankException()

        if created:
            self.order = self.publication.articles().all().count() + 1

        if not self.data:
            self.data = self.default_data

        if 'name' not in self.data:
            self.data['name'] = self.name

        self.assert_ids()
        validate_article(self.data)
        super(NewArticle, self).save(*args, **kwargs)

        if 'id' not in self.data:
            self.data['id'] = self.pk
            self.data['name'] = self.name
            self.save()
            return

        tasks.upload_new_publication.delay(self.publication.pk)

    @property
    def default_data(self):
        return {
            "sections": [
                {
                    "bg": {
                        "color": None,
                        "imageUrl": None,
                        "fullHeight": False
                    },
                    "columns": [
                        [
                            {
                                "classes": [],
                                "content": {
                                    "style": 'paragraph',
                                    "text": "First column, second block"
                                },
                                "type": "TextBlock"
                            },
                            {
                                "classes": [],
                                "content": {
                                    "style": 'paragraph',
                                    "text": "First column, first block"
                                },
                                "type": "TextBlock"
                            }
                        ],
                        [
                            {
                                "classes": [],
                                "content": {
                                    "style": 'paragraph',
                                    "text": "Second column, first block"
                                },
                                "type": "TextBlock"
                            }
                        ]
                    ],
                    "layout": "TwoCol",
                    "style": {}
                }
            ]
        }


def render_inline_publication(publication):
    return {
        'slug': publication.slug,
        'url': reverse('api-publication-detail', args=(publication.pk,)),
        'id': publication.pk,
        'name': publication.name
    }


def render_theme(theme):
    group = theme.group
    theme.data['stylesheet'] = theme.fonts_url
    publications = Publication.objects.filter(new_theme=theme)
    theme.data['publications'] = map(render_inline_publication, publications)
    theme.data['name'] = theme.name
    theme.data['id'] = theme.pk
    theme.data['group'] = {
        'name': group.name,
        'id': group.id,
        'url': group.get_absolute_url()
    }
    return {
        'theme': theme.data
    }


def render_inline_article(article):
    if not isinstance(article, NewArticle):
        return

    return {
        'name': article.name,
        'url': article.url
    }


@time_as('article.render-time')
def render_article(article):
    publication = article.publication
    group = publication.group
    theme = render_theme(publication.new_theme)['theme']

    inline_articles = map(render_inline_article, publication.articles().all())

    data = article.data
    data['liveUrl'] = article.rendered_url
    data['pdfUrl'] = None
    data['order'] = article.order
    data['orderHuman'] = int_to_string(article.order)

    nav = publication.nav
    nav['logo'] = group.logo_url() or None
    nav['navItems'] = publication.get_nav_items()

    return {
        'article': article.data,
        'publication': {
            'id': publication.pk,
            'name': publication.name,
            'slug': publication.slug,
            'url': publication.rest_api_url,
            'liveUrl': publication.get_new_style_preview_url(),
            'articles': inline_articles,
            'nav': nav
        },
        'group': {
            'id': group.pk,
            'name': group.name,
            'slug': group.slug
        },
        'theme': theme,
    }


def render_publication(publication):
    if not publication.new_style:
        return publication.json

    articles = map(render_inline_article, publication.articles().all())
    group = publication.group
    theme = publication.theme
    nav = publication.nav or publication.default_nav
    nav['logo'] = group.logo_url() or None
    nav['navItems'] = publication.get_nav_items()

    theme = render_theme(publication.new_theme)['theme']

    return {
        'publication': {
            'id': publication.pk,
            'name': publication.name,
            'created': publication.created,
            'modified': publication.modified,
            'pagination': publication.get_pagination_display().lower(),
            'articles': articles,
            'nav': nav
        },
        'group': {
            'id': group.pk,
            'name': group.name,
            'slug': group.slug
        },
        'theme': theme,
    }


@receiver(post_save, sender=Publication)
@receiver(post_save, sender=Article)
@receiver(post_save, sender=TextBlock)
@receiver(post_save, sender=PhotoBlock)
@receiver(post_save, sender=AudioBlock)
@receiver(post_save, sender=VideoBlock)
def publication_saved_handler(sender, instance, created, **kwargs):

    if sender in [TextBlock, PhotoBlock, AudioBlock, VideoBlock]:
        publication = instance.article.publication

    elif sender == Article:
        publication = instance.publication

    elif sender == Publication:
        publication = instance

    else:
        return

    key = 'publication:dict:{}'.format(publication.pk)

    if not cache.get(key, None):
        publication.cache_json()
        cache.set(key, True)
        publication.save()
    else:
        cache.delete(key)


@receiver(post_delete, sender=Publication)
@receiver(post_delete, sender=Article)
@receiver(post_delete, sender=TextBlock)
@receiver(post_delete, sender=PhotoBlock)
@receiver(post_delete, sender=AudioBlock)
@receiver(post_delete, sender=VideoBlock)
def model_deleted_handler(sender, instance, **kwargs):
    """
    Note: this runs in a transaction
    """
    if sender == Publication:
        Event.objects.filter(parent_publication=instance).delete()
        return

    if sender == Article:

        try:
            publication = instance.publication
            Event.objects.create(type=2, created_by=instance.created_by,
                                 parent_publication=publication)
        except Publication.DoesNotExist:
            publication = None

        # Delete all events that have the current instance as their
        # parent; PostgreSQL freaks out about integrity otherwise
        Event.objects.filter(parent_article=instance).delete()

        if publication:
            publication._fix_article_order_no_transaction()
    else:

        try:
            parent = instance.article
        except Article.DoesNotExist:
            return

        if parent.is_draft:
            return

        if sender == TextBlock:
            type = 7
        elif sender == PhotoBlock:
            type = 8
        elif sender == AudioBlock:
            type = 9
        elif sender == VideoBlock:
            type = 10
        else:
            type = None

        if type:
            Event.objects.create(type=type, created_by=instance.created_by,
                                 parent_article=parent)


@receiver(post_save, sender=Publication)
def trigger_screenshot_generation(sender, instance, **kwargs):
    if TESTING:
        return

    instance.render_jpg()


def index_text_block(tb):
    if not tb:
        return

    if tb.article.publication.status != 'live':
        return

    doc = tb.es_doc()

    es = get_es()

    if not es.indices.exists(index='blocks'):
        es.indices.create(index='blocks', body=tb.es_mapping)

    es.index(index='blocks', doc_type='block', id=tb.pk, body=doc)


def index_publication(publication):
    if not publication:
        return

    if publication.status != 'live':
        return

    doc = publication.es_doc()

    es = get_es()

    if not es.indices.exists(index='publications'):
        es.indices.create(index='publications', body=publication.es_mapping)

    es.index(index='publications', doc_type='publication', id=publication.pk,
             body=doc)


def format_es_hit(hit):
    if hit['_type'] == 'block':
        highlighted_content = hit['highlight']['content'][0]

        data = hit['_source']
        b = TextBlock.objects.get(pk=data['block_id'])

        data['score'] = hit['_score']
        data['link'] = b.link_to_block
        data['content'] = highlighted_content

    elif hit['_type'] == 'publication':
        highlighted_content = hit['highlight']['name'][0]
        data = hit['_source']
        publication = Publication.objects.get(pk=data['publication_id'])

        data['content'] = 'Publication name: ' + highlighted_content
        data['link'] = publication.get_share_url()
    else:
        data = None

    return data


def format_es_results(hits):
    return map(format_es_hit, hits)
