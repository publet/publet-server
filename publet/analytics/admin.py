from django.contrib import admin
from models import Event


class EventAdmin(admin.ModelAdmin):
    list_display = ('type', 'publication_id', 'article_id', 'block_id',
                    'user_id', 'anonymous_id', 'created',)
    list_filter = ('type',)

    class Meta:
        model = Event


admin.site.register(Event, EventAdmin)
