from datetime import datetime, timedelta
from django.utils.timezone import now
from django.test import TestCase
from models import GroupSubscriptionCoupon
from publet.groups.models import Group


class CouponTest(TestCase):

    def test_expiry(self):
        g = Group.objects.create(name='group')

        tz = now().tzinfo
        expiry = datetime(2013, 1, 1, 14, 0, 0, tzinfo=tz)

        c = GroupSubscriptionCoupon.objects.create(
            expires=expiry,
            group=g,
            new_price=12
        )

        self.assertTrue(c.is_expired)

        expiry = now() + timedelta(days=365 * 10)
        c.expires = expiry
        c.save()

        self.assertFalse(c.is_expired)

        c.expires = None
        c.save()
        self.assertFalse(c.is_expired)
