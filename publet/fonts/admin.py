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
from publet.fonts.models import Font, FontFile


class FontAdmin(admin.ModelAdmin):
    list_display = ('name', 'family', 'color',)
    search_fields = ('name',)


class FontFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'filename',)
    search_fields = ('filename',)


admin.site.register(Font, FontAdmin)
admin.site.register(FontFile, FontFileAdmin)
