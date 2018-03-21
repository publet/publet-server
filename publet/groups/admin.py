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
