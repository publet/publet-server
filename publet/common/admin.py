from django.contrib import admin
from models import Feature


class FeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'requires_staff',
                    'requires_superuser',)


admin.site.register(Feature, FeatureAdmin)
