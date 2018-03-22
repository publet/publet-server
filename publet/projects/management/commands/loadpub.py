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
"""
loadpub management command
==========================

This commands take a pseudo fixture produced by the dumppub command.

For each Article and Block instance, we check if an instance with
the same PK exists.  If it doesn't, we save it and continue.  If it does
exist, we check if the existing instance belongs to the right
Publication/Article.

If a possible data integrity error is detected, we die immediately.
"""
from django.core.management.base import BaseCommand, CommandError
from django.core import serializers

from publet.utils.utils import slugify_uniquely


class Command(BaseCommand):

    args = 'publication_dump'

    def log(self, msg):
        self.stdout.write(str(msg) + '\n')

    def handle(self, *args, **kwargs):

        if len(args) != 1:
            raise CommandError('Needs exactly one file')

        data = open(args[0]).read()

        models = list(serializers.deserialize('json', data))

        pub = None
        articles = {}

        for deserialized_obj in models:
            if deserialized_obj.object.__class__.__name__ == 'Publication':
                pub = deserialized_obj.object

        pub.save()
        self.log('Saving Publication')

        if not pub:
            raise CommandError('Lol, no Publication found in fixture')

        # Important: articles need to be saved first

        for deserialized_obj in models:
            obj = deserialized_obj.object
            Class = obj.__class__
            name = Class.__name__
            orig_pk = obj.pk

            if name == 'Article':
                try:
                    existing = Class.objects.get(pk=obj.pk)
                except Class.DoesNotExist:
                    self.log('Saving Article {}'.format(obj.pk))
                    articles[obj.pk] = obj.pk
                    deserialized_obj.save()
                    continue

                if existing.publication.pk == pub.pk:
                    self.log('Saving Article {}'.format(obj.pk))
                    articles[obj.pk] = obj.pk
                    deserialized_obj.save()
                else:
                    self.log('Saving Article {} resetting pk'.format(obj.pk))

                    obj.pk = None
                    obj.uuid = None

                    current_slug = obj.slug
                    try:
                        Class.objects.get(slug=current_slug)
                        self.log('Reslugifying')
                        obj.slug = slugify_uniquely(current_slug, Class)
                    except Class.DoesNotExist:
                        pass

                    obj.save()
                    articles[orig_pk] = obj.pk

        self.log('Articles are saved')

        for deserialized_obj in models:
            obj = deserialized_obj.object
            Class = obj.__class__
            name = Class.__name__
            orig_pk = obj.pk

            if name in ['Publication', 'Article']:
                continue
            elif name.endswith('Block'):
                supposed_parent_article_pk = articles[obj.article_id]
                obj.article_id = supposed_parent_article_pk

                try:
                    existing = Class.objects.get(pk=obj.pk)
                except Class.DoesNotExist:
                    self.log('Saving {} {} nc'.format(name, obj.pk))
                    obj.save()
                    continue

                self.log('Saving {} {}'.format(name, obj.pk))
                obj.id = None
                obj.save()

            else:
                raise CommandError('Not sure what to do with {}'.format(name))

        self.log('All done and it was a great success')
