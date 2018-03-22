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
from publet.groups.models import Group, GroupMember, GroupHub


class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'members_count',)


class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'role',)
    search_fields = ('user__username', 'group__name',)
    list_filter = ('role',)


class GroupHubAdmin(admin.ModelAdmin):
    pass


admin.site.register(Group, GroupAdmin)
admin.site.register(GroupMember, GroupMemberAdmin)
admin.site.register(GroupHub, GroupHubAdmin)
