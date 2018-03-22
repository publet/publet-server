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
from django.db import models
from django.core.cache import cache
from django.conf import settings
from django.forms.models import model_to_dict
from annoying.functions import get_object_or_None

User = settings.USER_MODEL


class ModelDiffMixin(object):
    """
    A model mixin that tracks model fields' values and provide some
    useful api to know what fields have been changed.
    """

    def __init__(self, *args, **kwargs):
        super(ModelDiffMixin, self).__init__(*args, **kwargs)

        self.fields = [f.name for f in filter(
            lambda f: not isinstance(f, models.ManyToManyField),
            self._meta.fields)]

        self.__initial = self._dict

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    @property
    def _dict(self):
        return model_to_dict(self, fields=self.fields)


class BaseModel(models.Model, ModelDiffMixin):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, null=True)

    always_save = False

    class Meta:
        abstract = True

    def duplicate(self, **kwargs):
        new_kwargs = []
        ignore = ['id', 'uuid', 'slug']

        for field in self._meta.fields:
            if field.name in ignore:
                continue

            new_kwargs.append((field.name, getattr(self, field.name)))

        kwargs = dict(new_kwargs)
        return self.__class__.objects.create(**kwargs)

    @property
    def as_dict_cache_key(self):
        return '{}.{}:{}'.format(self.__class__.__module__,
                                 self.__class__.__name__,
                                 self.pk)

    def as_dict(self):
        value = cache.get(self.as_dict_cache_key, None)

        if not value:
            excludes = ('id', 'created', 'modified',)
            items = []

            for f in self._meta.fields:
                if f.name in excludes:
                    continue

                items.append((f.name, getattr(self, f.name),))

            value = dict(items)
            cache.set(self.as_dict_cache_key, value)

        return value

    def save(self, *args, **kwargs):
        if self.pk and not self.always_save and not self.has_changed:
                return self

        super(BaseModel, self).save(*args, **kwargs)
        self.__initial = self._dict
        cache.delete(self.as_dict_cache_key)


class FeatureManager(models.Manager):

    def as_dict(self, qs):
        return dict([(str(f.slug), f.as_dict(),) for f in qs])


class Feature(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=False)
    requires_staff = models.BooleanField(default=False)
    requires_superuser = models.BooleanField(default=False)

    objects = FeatureManager()

    def as_dict(self):
        return {
            'name': self.name,
            'slug': self.slug,
            'is_active': self.is_active,
            'requires_staff': self.requires_staff,
            'requires_superuser': self.requires_superuser
        }


def feature_active(request, feature_slug=None, feature=None):
    """
    Can be called with feature_slug or feature (dict or instance)
    """
    if not feature_slug and not feature:
        return False

    if not feature:
        feature = get_object_or_None(Feature, slug=feature_slug)

        if not feature:
            return False

    if not isinstance(feature, dict):
        feature = feature.as_dict()

    if not feature['is_active']:
        return False

    if not request.user.is_staff and feature['requires_staff']:
        return False

    if not request.user.is_superuser and feature['requires_superuser']:
        return False

    return True


class CDNMixin(object):

    def ensure_cdn_links(self, field_name):
        f = 'https://www.filepicker.io'
        cdn = 'https://cdn.publet.com'

        if not hasattr(self, field_name):
            return

        value = getattr(self, field_name, None)

        if value and value.startswith(f):
            setattr(self, field_name, value.replace(f, cdn))
