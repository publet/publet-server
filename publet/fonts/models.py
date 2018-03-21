import os

from django.db import models
from django.template.defaultfilters import slugify
from publet.common.models import BaseModel
from publet.common.fields import FilePickerField
from publet.utils.utils import get_filepicker_read_policy


FILEPICKER_READ_POLICY, FILEPICKER_READ_SIGNATURE = \
    get_filepicker_read_policy()


FONT_STYLES = (
    ('normal', 'normal',),
    ('italic', 'italic',),
    ('bold', 'bold',),
    ('italic-bold', 'italic-bold',),
)


def urlize_font(name):
    """
    Open Sans => Open+Sans
    """
    return name.replace(' ', '+')


class FontFile(BaseModel):
    file = FilePickerField()
    filename = models.CharField(max_length=255)
    style = models.CharField(max_length=11, choices=FONT_STYLES,
                             default='normal')

    def __unicode__(self):
        return self.filename

    @property
    def ext(self):
        return os.path.splitext(self.filename)[1][1:]

    @property
    def format(self):
        if self.ext == 'otf':
            return 'opentype'
        elif self.ext == 'ttf':
            return 'truetype'
        return self.ext

    @property
    def url(self):
        return '%s?signature=%s&policy=%s' % (
            self.file,
            FILEPICKER_READ_SIGNATURE,
            FILEPICKER_READ_POLICY)

    def ensure_cdn_links(self):
        f = 'https://www.filepicker.io'
        cdn = 'https://cdn.publet.com'

        if self.file and self.file.startswith(f):
            self.file = self.file.replace(f, cdn)

    def save(self, *args, **kwargs):
        self.ensure_cdn_links()

        super(FontFile, self).save(*args, **kwargs)


class Font(BaseModel):
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True, null=True)
    family = models.CharField(max_length=255, blank=True)
    color = models.CharField(max_length=255, blank=True)
    files = models.ManyToManyField(FontFile, blank=True)

    def __unicode__(self):
        return self.name

    def get_files(self):
        files = self.files.all()

        if files.count() == 1:
            return files

        return files.filter(style='normal')

    @property
    def slug(self):
        return slugify(self.name)

    @property
    def css(self):
        return 'font-family: \'{}\';'.format(self.family_name)

    @property
    def family_name(self):
        return self.family or self.name

    @property
    def is_google_font(self):
        return 'google' in self.url

    @property
    def has_files(self):
        return self.files.all().exists()

    @property
    def https_url(self):
        if self.url.startswith('https'):
            return self.url

        return self.url.replace('http', 'https')

    @property
    def agnostic_url(self):
        """
        E.g. //fonts.googleapis.com/css?family=Open+Sans
        """
        return self.https_url.replace('https:', '')

    @classmethod
    def create_default_fonts(cls):
        template = 'https://fonts.googleapis.com/css?family='
        fonts = [
            ('Lato', 'Lato',),
            ('Lora', 'Lora',),
            ('Merriweather', 'Merriweather',),
            ('Oswald', 'Oswald',),
            ('Open Sans:300,400,700', 'Open Sans',),
        ]

        objs = []

        for f, family in fonts:
            obj = cls.objects.create(name=f, family=family, url=template +
                                     urlize_font(f))
            objs.append(obj)

        system_fonts = [
            'Georgia',
            'Arial',
            'Times New Roman'
        ]

        for f in system_fonts:
            obj = cls.objects.create(name=f, family=f)
            objs.append(obj)

        return objs
