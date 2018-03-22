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
import zipfile
from StringIO import StringIO
from datetime import datetime

from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect

from tastypie.models import ApiKey

from publet.projects.models import (
    Article, Type, TextBlock, Theme, PhotoBlock, VideoBlock, AudioBlock,
    Publication, Color, Preset, PresetItem, Photo, Readability, Flavor, Event,
    PublicationSocialGateEntry, PDFUpload,
    PublicationSlug, GateSubmission, NewArticle, NewTheme
)
from publet.projects import tasks


class PresetItemInline(admin.TabularInline):
    model = PresetItem


class PublicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'theme', 'slug', 'published',
                    'modified',)
    actions = ['export_purchases', 'change_group']
    search_fields = ('name',)
    list_filter = ('new_style',)

    def get_actions(self, request):
        actions = super(PublicationAdmin, self).get_actions(request)

        if not request.user.has_perm('projects.change_publication'):
            actions.pop('change_group')

        return actions

    def export_purchases(self, request, queryset):

        z = StringIO()
        zip_file = zipfile.ZipFile(z, 'w')

        date = datetime.utcnow().strftime('%Y%m%d-%H%M%S')

        directory = 'publet-export-{}'.format(date)

        for publication in queryset:
            fn = '{}/{}.csv'.format(directory, publication.slug)
            zip_file.writestr(fn, publication.export_purchases())

        zip_file.close()
        z.seek(0)

        r = HttpResponse(z, content_type='application/zip')
        r['Content-Disposition'] = 'attachment; filename="publet-export.zip"'

        return r

    export_purchases.short_description = 'Export purchases'

    def change_group(self, request, queryset):
        if queryset.count() > 1:
            messages.error(request, "Please select only one publication")
            return redirect('admin:projects_publication_changelist')

        p = queryset[0]
        return redirect('admin-change-group', p.pk)

    change_group.short_description = 'Change group'


class TypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class ThemeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    actions = ['update_theme', 'disassociate']

    def get_actions(self, request):
        actions = super(ThemeAdmin, self).get_actions(request)

        if not request.user.has_perm('projects.delete_theme'):
            actions.pop('delete_selected')
            actions.pop('disassociate')

        return actions

    def update_theme(self, request, queryset):
        if not request.user.has_perm('projects.update_theme_on_disk'):
            return HttpResponseForbidden()

        for theme in queryset:
            theme.update_theme_on_disk(collect_static=False)

        tasks.collectstatic.delay()

        self.message_user(
            request,
            '{} file(s) successfully updated'.format(len(queryset)))

    update_theme.short_description = 'Update theme on disk'

    def disassociate(self, request, queryset):
        for theme in queryset:
            theme.disassociate()

        self.message_user(
            request,
            '{} theme(s) successfully updated'.format(len(queryset)))

    disassociate.short_description = 'Disassociate objects from theme'

    def save_model(self, request, obj, form, change):
        obj.save()
        obj.ensure_theme_on_disk()


class ArticleAdmin(admin.ModelAdmin):
    list_display = ('name', 'preset', 'theme', 'slug', 'publication',)
    search_fields = ('name',)


class CodeBlockAdmin(admin.ModelAdmin):
    list_display = ('article', 'order',)


class ColorsBlockAdmin(admin.ModelAdmin):
    list_display = ('article', 'order',)


class HeadingBlockAdmin(admin.ModelAdmin):
    list_display = ('article', 'order',)


class ImageAssetAdmin(admin.ModelAdmin):
    list_display = ('image_asset_block',)


class ImageAssetBlockAdmin(admin.ModelAdmin):
    list_display = ('article', 'order',)


class PhotoBlockAdmin(admin.ModelAdmin):
    list_display = ('article', 'order',)


class PhotoAdmin(admin.ModelAdmin):
    list_display = ('block', 'heading', 'image', 'description',)


class PullquoteBlockAdmin(admin.ModelAdmin):
    list_display = ('article', 'order',)


class TextBlockAdmin(admin.ModelAdmin):
    list_display = ('article', 'order',)


class VideoBlockAdmin(admin.ModelAdmin):
    list_display = ('article', 'order', 'video_url', 'width', 'height',)


class AudioBlockAdmin(admin.ModelAdmin):
    list_display = ('article', 'order', 'audio_url',)


class FontsBlockAdmin(admin.ModelAdmin):
    list_display = ('article', 'order', 'name', 'file',)


class ColorAdmin(admin.ModelAdmin):
    list_display = ('hex',)
    search_fields = ('hex',)


class PresetAdmin(admin.ModelAdmin):
    list_display = ('name', 'should_appear_in_output',)
    inlines = [PresetItemInline]


class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'key',)
    search_fields = ('user__username',)


class FlavorAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'theme',)
    search_fields = ('name',)


class EventAdmin(admin.ModelAdmin):
    list_display = ('type', 'parent_article', 'parent_publication', 'created',
                    'created_by',)


class PublicationSocialGateEntryAdmin(admin.ModelAdmin):
    list_display = ('publication', 'block_id', 'name', 'referrer',)


class PDFUploadAdmin(admin.ModelAdmin):
    list_display = ('filename', 'publication', 'created',)


class GateSubmissionAdmin(admin.ModelAdmin):
    list_display = ('publication', 'data', 'created',)


class PublicationSlugAdmin(admin.ModelAdmin):
    list_display = ('slug', 'publication',)


class NewArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'publication', 'order',)
    actions = ['reset_article']

    def reset_article(self, request, queryset):
        for article in queryset:
            article.data = article.default_data
            article.save()

        self.message_user(
            request,
            '{} articles have been reset.'.format(len(queryset)))

    reset_article.short_description = 'Reset article(s) to default data'


class NewThemeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'group',)

    actions = ['reset_theme']

    def reset_theme(self, request, queryset):
        for theme in queryset:
            theme.data = theme.default_data
            theme.save()

        self.message_user(
            request,
            '{} themes have been reset.'.format(len(queryset)))

    reset_theme.short_description = 'Reset theme(s) to default data'


admin.site.register(Publication, PublicationAdmin)
admin.site.register(Type, TypeAdmin)
admin.site.register(Theme, ThemeAdmin)
admin.site.register(Article, ArticleAdmin)

admin.site.register(PhotoBlock, PhotoBlockAdmin)
admin.site.register(TextBlock, TextBlockAdmin)
admin.site.register(VideoBlock, VideoBlockAdmin)
admin.site.register(AudioBlock, AudioBlockAdmin)
admin.site.register(Color, ColorAdmin)
admin.site.register(Preset, PresetAdmin)
admin.site.register(Photo)
admin.site.register(Readability)
admin.site.unregister(ApiKey)
admin.site.register(ApiKey, ApiKeyAdmin)
admin.site.register(Flavor, FlavorAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(PublicationSocialGateEntry,
                    PublicationSocialGateEntryAdmin)
admin.site.register(PDFUpload, PDFUploadAdmin)
admin.site.register(PublicationSlug, PublicationSlugAdmin)
admin.site.register(GateSubmission, GateSubmissionAdmin)
admin.site.register(NewArticle, NewArticleAdmin)
admin.site.register(NewTheme, NewThemeAdmin)
