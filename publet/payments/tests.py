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
