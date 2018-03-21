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
