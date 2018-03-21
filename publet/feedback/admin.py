from django.contrib import admin
from models import Feedback


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('type', 'message', 'created_by', 'created',)


admin.site.register(Feedback, FeedbackAdmin)
