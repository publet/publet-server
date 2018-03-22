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
from django.contrib import admin
from models import PubletUser, PubletApiKey
from django.contrib.auth.admin import UserAdmin


class PubletUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email',
                    'is_superuser', 'account_type',)
    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups',
                   'account_type',)
    filter_horizontal = ('groups', 'user_permissions',)
    ordering = ('username',)

    def lookup_allowed(self, lookup, value):
        if lookup.startswith('password'):
            return False
        return super(PubletUserAdmin, self).lookup_allowed(lookup, value)

    class Meta:
        model = PubletUser


class PubletApiKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created',)

    class Meta:
        model = PubletApiKey


admin.site.register(PubletUser, PubletUserAdmin)
admin.site.register(PubletApiKey, PubletApiKeyAdmin)
