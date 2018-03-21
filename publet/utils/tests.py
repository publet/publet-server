from django.test import TestCase
from django.contrib.auth import get_user_model
from utils import get_filepicker_read_policy
from models import BulkUserUpload, UserAccountRequest, Welcome
from publet.projects.models import Type, Publication, Theme
from publet.groups.models import Group, GroupMember
from publet.payments.models import Purchase


class PolicyTest(TestCase):

    def test_read_policy(self):
        p, s = get_filepicker_read_policy()

        p2, s2 = get_filepicker_read_policy()

        self.assertEquals(p, p2)
        self.assertEquals(s, s2)


class PermissionTest(TestCase):

    def test_can_create_type(self):
        user = get_user_model().objects.create(username='test',
                                               email='test@test.com')

        t = Type.objects.create(name='Identity')

        self.assertEquals('R', user.account_type)

        user.account_type = 'B'
        user.save()

        self.assertTrue(user.can_create_publication_type(t))

        t.name = 'XXX'
        t.save()

        self.assertFalse(user.can_create_publication_type(t))

        user.account_type = 'P'
        user.save()

        self.assertTrue(user.can_create_publication_type(t))


class CSVTest(TestCase):

    def setUp(self):
        self.data = """john,smith,john.smith@gmail.com
jane,smith,jane.smith@gmail.com
        """
        self.group = Group.objects.create(name='Test group')
        self.pub_type = Type.objects.create(name='pub type')
        self.theme = Theme.objects.create(name='Default')

        self.pub = Publication.objects.create(
            name='Test publication',
            group=self.group,
            type=self.pub_type,
            theme=self.theme)

    def test_parsing(self):
        b = BulkUserUpload(csv_data=self.data, message="hey")
        b.save()

        parsed = b.parse_csv()

        self.assertEquals(2, len(parsed))
        self.assertEquals(3, len(parsed[0]))

        self.assertEquals(2, UserAccountRequest.objects.count())

        uar = UserAccountRequest.objects.all()[0]

        self.assertEquals(uar.first, 'john')
        self.assertEquals(uar.last, 'smith')
        self.assertEquals(uar.email, 'john.smith@gmail.com')
        self.assertEquals(uar.user, None)
        self.assertEquals(uar.upload.pk, b.pk)

        b.save()
        self.assertEquals(2, UserAccountRequest.objects.count())

        # Second one

        b2 = BulkUserUpload(csv_data=self.data, message="yo")
        b2.save()

        uar = UserAccountRequest.objects.all()[0]
        self.assertEquals(uar.upload.pk, b.pk)

        uar.user = get_user_model().objects.create(username='abc')
        uar.save()

        b.publications.add(self.pub)

        self.assertEquals(0, Purchase.objects.count())
        b.save()
        self.assertEquals(1, Purchase.objects.count())

    def test_purchases(self):
        b = BulkUserUpload(csv_data=self.data, message="hey", stripe_id="abc")
        b.save()

        b.publications.add(self.pub)
        b.save()

        # -----

        self.assertEquals(0, Purchase.objects.count())

        uar = UserAccountRequest.objects.all()[0]
        uar.user = get_user_model().objects.create(username='test',
                                                   email='test')
        uar.add_purchases()

        self.assertEquals(1, Purchase.objects.count())

        uar.add_purchases()
        self.assertEquals(1, Purchase.objects.count())

    def test_groups(self):
        group = Group.objects.create(name='Test group')

        b = BulkUserUpload(csv_data=self.data, message="hey", stripe_id="abc")
        b.save()
        b.groups.add(group)
        b.save()

        # -----

        self.assertEquals(0, GroupMember.objects.count())

        uar = UserAccountRequest.objects.all()[0]
        uar.user = get_user_model().objects.create(username='test',
                                                   email='test')
        uar.add_groups()

        self.assertEquals(1, GroupMember.objects.count())
