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
