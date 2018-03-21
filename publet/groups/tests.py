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
