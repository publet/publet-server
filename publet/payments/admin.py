from django.contrib import admin
from publet.payments.models import (
    Purchase, PublicationCoupon, GroupSubscriptionCoupon
)


class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'publication', 'stripe_id',)
    list_filter = ('group', 'created', 'purchase_type',)
    search_fields = ('user__username',)

    def save_model(self, request, obj, form, change):
        obj.save(skip_receipt=True)


class PublicationCouponAdmin(admin.ModelAdmin):
    list_display = ('publication', 'code', 'expires', 'is_active',
                    'new_price',)


class GroupSubscriptionCouponAdmin(admin.ModelAdmin):
    list_display = ('group', 'code', 'expires', 'is_active', 'new_price',)


admin.site.register(Purchase, PurchaseAdmin)
admin.site.register(PublicationCoupon, PublicationCouponAdmin)
admin.site.register(GroupSubscriptionCoupon, GroupSubscriptionCouponAdmin)
