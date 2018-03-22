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
import csv
from StringIO import StringIO

from django import forms
from django.contrib import admin
from django.conf import settings
from django.http import HttpResponse

from publet.utils.utils import send_welcome_email
from publet.utils.models import (
    BulkUserUpload, UserAccountRequest, Invite, Welcome, generate_code,
    Simulation, Signup, Embed, TooManyEmbedsExceptions
)


DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
HOST = getattr(settings, 'HOST', None)


def notify(modeladmin, request, queryset):
    bulk = queryset[0].upload
    bulk.notify(qs=queryset)


notify.short_description = 'Notify selected users by email'


def welcome_email(modeladmin, request, queryset):
    queryset = queryset.filter(user__isnull=False)

    for uar in queryset:
        send_welcome_email(uar.user, request)


welcome_email.short_description = 'Send welcome email to selected users'


class UserAccountRequestAdmin(admin.ModelAdmin):
    list_display = ('first', 'last', 'email', 'notified', 'fulfilled', 'user',)
    actions = [notify, welcome_email]
    search_fields = ('first', 'last', 'email',)
    list_filter = ('notified',)
    ordering = ('created',)


class BulkUserUploadAdmin(admin.ModelAdmin):
    list_display = ('name', 'stripe_id', 'created', 'created_via_admin',)
    exclude = ('created_via_admin',)

    def save_model(self, request, obj, form, change):
        obj.created_via_admin = True
        obj.save()


class InviteAdminForm(forms.ModelForm):
    number = forms.IntegerField()

    class Meta:
        model = Invite
        fields = '__all__'


class InviteAdmin(admin.ModelAdmin):
    filter_horizontal = ('groups', 'publications',)
    list_display = ('code', 'active', 'user', 'user_type', 'user_role',)
    list_filter = ('user_type', 'active',)
    actions = ['download_csv']
    form = InviteAdminForm

    def save_related(self, request, form, formsets, change):
        pass

    def save_model(self, request, obj, form, change):
        number = form.cleaned_data['number']
        user_type = form.cleaned_data['user_type']
        user_role = form.cleaned_data['user_role']
        active = form.cleaned_data['active']
        publications = form.cleaned_data['publications']
        groups = form.cleaned_data['groups']

        for _ in range(number):
            invite = Invite.objects.create(code=generate_code(), active=active,
                                           user_type=user_type,
                                           user_role=user_role)
            for pub in publications:
                invite.publications.add(pub)

            for group in groups:
                invite.groups.add(group)

    def download_csv(self, request, queryset):
        f = StringIO()

        writer = csv.writer(f)

        for obj in queryset:
            if obj.user:
                user = obj.user.username
            else:
                user = 'none'

            writer.writerow([
                obj.code,
                obj.user_type,
                obj.active,
                user])

        f.seek(0)

        r = HttpResponse(f, content_type='text/csv')
        r['Content-Disposition'] = 'attachment; filename="invites.csv"'

        return r

    download_csv.short_description = 'Download CSV'


class WelcomeAdmin(admin.ModelAdmin):
    list_display = ('account_type', 'publication_count')


class SimulationAdmin(admin.ModelAdmin):
    list_display = ('name', 'number_of_simulations',)
    actions = ['apply']

    def apply(self, request, queryset):
        for obj in queryset:
            obj.apply()

    apply.short_description = 'Apply simulation'


class SignupAdmin(admin.ModelAdmin):
    list_display = ('first_name_and_last_name', 'organization', 'email',
                    'created',)


class EmbedAdmin(admin.ModelAdmin):
    list_display = ('publication', 'created',)

    def save_model(self, request, obj, form, change):
        try:
            obj.save()
        except TooManyEmbedsExceptions:
            self.message_user(request,
                              'Only one embed can be active at a time.')


admin.site.register(BulkUserUpload, BulkUserUploadAdmin)
admin.site.register(UserAccountRequest, UserAccountRequestAdmin)
admin.site.register(Invite, InviteAdmin)
admin.site.register(Welcome, WelcomeAdmin)
admin.site.register(Simulation, SimulationAdmin)
admin.site.register(Signup, SignupAdmin)
admin.site.register(Embed, EmbedAdmin)
