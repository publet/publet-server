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
from django.test import TestCase
from django.contrib.auth import get_user_model

from models import Group, GroupMember


User = get_user_model()


def refresh(obj):
    if not obj.pk:
        raise Exception('no pk')

    return obj.__class__.objects.get(pk=obj.pk)


class PermissionsTest(TestCase):

    def test_superuser(self):
        u = User.objects.create(username='test', email='test@test.com',
                                is_superuser=True)

        g = Group.objects.create(name='test')

        GroupMember.objects.all().delete()
        member = GroupMember.objects.create(group=g, user=u, role='C')

        self.assertTrue(member.can_user_edit_group())
        self.assertTrue(member.can_user_invite_users_to_group())
        self.assertTrue(member.can_user_create_publications())
        self.assertTrue(member.can_user_edit_publication_settings())
        self.assertTrue(member.can_user_view_publication_data())
        self.assertTrue(member.can_user_download_formats())
        self.assertTrue(member.can_user_delete_articles())

        u.is_superuser = False
        u.save()

        member = refresh(member)

        self.assertFalse(member.can_user_edit_group())
        self.assertFalse(member.can_user_invite_users_to_group())
        self.assertFalse(member.can_user_create_publications())
        self.assertFalse(member.can_user_edit_publication_settings())
        self.assertFalse(member.can_user_view_publication_data())
        self.assertFalse(member.can_user_download_formats())
        self.assertFalse(member.can_user_delete_articles())
