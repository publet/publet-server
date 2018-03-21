import logging
import json
import csv
import random
from datetime import datetime
from StringIO import StringIO

import requests
from django.db import models, IntegrityError
from django.core.urlresolvers import reverse
from django.core.mail import send_mass_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from uuidfield import UUIDField
# from registration.signals import user_activated

from publet.common.models import BaseModel
from publet.groups.models import Group, GroupMember
from publet.projects.models import Publication, Article
# from publet.utils.utils import send_welcome_email
from publet.utils.fn import flatten
from publet.utils import tasks
from publet.payments.models import Purchase

User = settings.USER_MODEL
logger = logging.getLogger(__name__)


DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
HOST = getattr(settings, 'HOST', None)
SLACK_WEBHOOK_SALES = getattr(settings, 'SLACK_WEBHOOK_SALES', None)
INSTALLATION = getattr(settings, 'INSTALLATION', None)

CODE_LENGTH = 6
CODE_CHARSET = ''.join([
    'abcdefghjkmnpqrstuvwxyz',
    'ABCDEFGHJKMNPQRSTUVWXYZ',
    '123456789'])


def generate_code():
    chars = [random.choice(CODE_CHARSET) for i in xrange(CODE_LENGTH)]
    return ''.join(chars)


ACCOUNT_TYPES = (
    ('B', 'Basic'),
    ('P', 'Pro'),
    ('R', 'Reader'),
    ('T', 'Trial'),
    ('F', 'Free'),
)


ROLES = (
    ('O', 'Owner'),
    ('A', 'Admin'),
    ('C', 'Contributor'),
)

# NOTE: This is disabled because a client said it was buggy.
# We're not sure what's buggy about it.
# https://github.com/publet/publet/issues/1697
# user_activated.connect(send_welcome_email)


class BulkUserUpload(models.Model):
    help_text = """This is the message that will be sent to the user asking
    them to activate their account.  You can use Python's {} string
    interpolation syntax to place some variables in.  You can use {first},
    {last}, {email}, {groups} and {link}.
    """
    csv_help_text = "first,last,email"

    default_message = """Hello, {first} {last}

You have been invited to collaborate on {groups} publications using publet.com.

Activate your account to get started:

{link}"""

    name = models.CharField(max_length=255, blank=True)
    stripe_id = models.CharField(max_length=255, blank=True)
    publications = models.ManyToManyField(Publication, blank=True)
    csv_data = models.TextField(help_text=csv_help_text)
    message = models.TextField(help_text=help_text, blank=True,
                               default=default_message)
    account_type = models.CharField(max_length=1, choices=ACCOUNT_TYPES,
                                    default='R')
    group_role = models.CharField(max_length=1, choices=ROLES, blank=True)

    groups = models.ManyToManyField(
        Group, blank=True,
        help_text="A list of groups the user will have access to.")

    created_via_admin = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def parse_csv(self):
        if not self.csv_data:
            return None

        f = StringIO(self.csv_data.strip())
        reader = csv.reader(f)

        return [row for row in reader]

    def save(self, *args, **kwargs):
        skip_creation = kwargs.pop('skip_creation', False)
        rows = self.parse_csv()

        if self.group_role == '?':
            self.group_role = 'C'

        if not rows:
            raise ValueError('Invalid CSV data provided')

        for row in rows:
            try:
                assert len(row) == 3
            except AssertionError:
                raise ValueError('Invalid CSV data provided')

        super(BulkUserUpload, self).save(*args, **kwargs)

        if not skip_creation:
            self.create_requests(rows)

    def create_requests(self, rows):
        for row in rows:
            obj, created = UserAccountRequest.objects.get_or_create(
                email=row[2])

            # If a user with that email address already exists, just add them
            if not obj.user:
                try:
                    obj.user = get_user_model().objects.get(email=row[2])
                except get_user_model().DoesNotExist:
                    pass

            if created:
                obj.upload = self
                obj.first = row[0]
                obj.last = row[1]

                obj.save()

            if obj.user:
                obj.add_purchases()

    def notify(self, qs=None):
        if not qs:
            qs = self.useraccountrequest_set.all()

        qs = qs.filter(user__isnull=True)
        emails = []

        groups = self.groups.all()
        groups = ', '.join([g.name for g in groups])

        for uar in qs:
            activate_url = reverse('activate', kwargs=dict(uuid=uar.uuid))

            context = dict(first=uar.first, last=uar.last, email=uar.email,
                           link=HOST + activate_url, groups=groups)

            msg = ('Create your account', self.message.format(**context),
                   DEFAULT_FROM_EMAIL, [uar.email],)

            emails.append(msg)

        send_mass_mail(emails, fail_silently=False)

        qs.update(notified=True)


class UserAccountRequest(models.Model):
    first = models.CharField(max_length=255)
    last = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)

    notified = models.BooleanField(default=False)
    uuid = UUIDField(blank=True, null=True, max_length=12, auto=True,
                     unique=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    user = models.ForeignKey(User, null=True, blank=True)
    upload = models.ForeignKey(BulkUserUpload, null=True)
    fulfilled = models.DateTimeField(blank=True, null=True)

    def add_purchases(self):
        publications = self.upload.publications.all()

        for publication in publications:
            Purchase.objects.get_or_create(user=self.user,
                                           publication=publication,
                                           purchase_type='publication',
                                           stripe_id=self.upload.stripe_id)

        self.fulfilled = datetime.now()
        self.save()

    def add_groups(self):
        members = []

        role = self.upload.group_role or 'C'

        for group in self.upload.groups.all():
            members.append(GroupMember(group=group, user=self.user, role=role))

        GroupMember.objects.bulk_create(members)


class Invite(models.Model):
    code = models.CharField(max_length=100, unique=True, blank=True,
                            editable=False)
    active = models.BooleanField(default=False)
    user = models.ForeignKey(User, null=True, blank=True, editable=False)
    user_type = models.CharField(max_length=1, choices=ACCOUNT_TYPES,
                                 default='B')
    user_role = models.CharField(max_length=1, choices=ROLES, default='C')
    groups = models.ManyToManyField(Group, blank=True)
    publications = models.ManyToManyField(Publication, blank=True)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return self.code

    @property
    def is_redeemed(self):
        return self.user is not None

    def add_purchases(self):
        if self.publications:
            for pub in self.publications.all():
                purchase = Purchase(user=self.user, publication=pub,
                                    purchase_type='publication')
                purchase.save(skip_receipt=True)

    def add_groups(self):
        if not self.groups:
            return

        for group in self.groups.all():
            GroupMember.objects.create(user=self.user, group=group,
                                       role=self.user_role)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_code()

        super(Invite, self).save(*args, **kwargs)


class WelcomeManager(models.Manager):

    def run_for_user(self, user):
        return self._welcome_for_free(user)

        # try:
        #     welcome = self.get(account_type=user.account_type)
        # except Welcome.DoesNotExist:
        #     raise ValueError('Welcome instances not present')

        # publications = welcome.publications.all()

        # if not publications:
        #     return

        # if user.is_reader:
        #     return self._welcome_for_reader(user, publications)
        # elif user.is_basic:
        #     return self._welcome_for_basic(user, publications)
        # elif user.is_pro:
        #     return self._welcome_for_pro(user, publications)
        # elif user.is_trial:
        #     return self._welcome_for_trial(user, publications)
        # elif user.is_free:
        #     return self._welcome_for_free(user, publications)
        # else:
        #     raise TypeError('Wrong account type')

    def _welcome_for_reader(self, user, publications):
        purchases = []

        for publication in publications:
            p = Purchase(user=user, group=None, publication=publication,
                         purchase_type='publication')
            purchases.append(p)

        Purchase.objects.bulk_create(purchases)

    def _welcome_for_basic(self, user, publications):
        group = Group.objects.create(name=user.username)
        GroupMember.objects.create(group=group, user=user, role='O')

        for publication in publications:
            new_pub = publication.duplicate(prepend_copy=False)
            new_pub.group = group
            new_pub.save()

    def _welcome_for_pro(self, user, publications):
        return self._welcome_for_basic(user, publications)

    def _welcome_for_trial(self, user, publications):
        return self._welcome_for_pro(user, publications)

    def _welcome_for_free(self, user):
        group = Group.objects.create(name=user.username)
        GroupMember.objects.create(group=group, user=user, role='O')
        Publication.create_welcome_publication(group, user)


class Welcome(models.Model):
    account_type = models.CharField(max_length=1, choices=ACCOUNT_TYPES,
                                    default='R')

    publications = models.ManyToManyField(Publication)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    objects = WelcomeManager()

    def __unicode__(self):
        return self.get_account_type_display()

    @property
    def publication_count(self):
        return self.publications.count()


class Simulation(models.Model):
    name = models.CharField(max_length=255)
    publications = models.ManyToManyField(Publication)
    number_of_simulations = models.IntegerField(default=10)

    def __unicode__(self):
        return self.name

    def apply(self):
        group, _ = Group.objects.get_or_create(name='Simulations')
        publications = self.publications.all()

        articles = Article.objects.filter(
            publication__in=publications).distinct()

        blocks = flatten([a.get_blocks() for a in articles])

        for x in range(0, self.number_of_simulations):
            p = Publication.objects.create(
                name='simulation-{}-{}'.format(self.pk, x), group=group)

            num_articles = random.randint(1, 10)

            for y in range(0, num_articles):
                name = 'simulation-{}-{}-{}'.format(self.pk, x, y)
                a = Article.objects.create(name=name, publication=p,
                                           group=group, order=y)

                num_blocks = random.randint(1, 20)

                for z in range(0, num_blocks):
                    block = random.choice(blocks)
                    block.duplicate(article=a)

        staff_users = get_user_model().objects.filter(is_staff=True)

        for user in staff_users:
            try:
                GroupMember.objects.get_or_create(group=group, role='O',
                                                  user=user)
            except IntegrityError:
                pass


class Signup(BaseModel):
    first_name_and_last_name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)

    def message(self):
        return "{} from {} just signed up with {}".format(
            self.first_name_and_last_name, self.organization, self.email
        )

    def send_slack_message(self):
        if not SLACK_WEBHOOK_SALES:
            logger.error('slack webhook not configured')
            return

        data = {
            'username': 'Signupbot',
            'attachments': [{
                'fields': [{
                    'title': 'New signup',
                    'value': self.message(),
                    'short': False
                }]
            }]
        }

        payload = json.dumps(data)
        requests.post(SLACK_WEBHOOK_SALES, data=payload)

    def submit_to_close(self):
        url = 'https://app.close.io/api/v1/lead/'
        auth = ('fe924e84bf63a5ee44aaa069873840bed0497e1480aee9c40e2cb681', '')

        data = {
            'name': self.organization,
            'status': 'Qualified',
            'contacts': [
                {
                    'name': self.first_name_and_last_name,
                    'title': 'Unknown',
                    'emails': [
                        {
                            'type': 'office',
                            'email': self.email
                        }
                    ]
                }
            ],
            'custom': {
                'source_lead': 'Signup'
            }
        }

        r = requests.post(url, auth=auth, data=json.dumps(data))

        if r.status_code != 200:
            raise Exception("Couldn't create lead")

        lead_id = r.json()['id']

        url = 'https://app.close.io/api/v1/opportunity/'

        data = {
            'status': 'Pending',
            'lead_id': lead_id
        }

        r = requests.post(url, auth=auth, data=json.dumps(data))

        if r.status_code != 200:
            raise Exception("Couldn't create opportunity")

        url = 'https://app.close.io/api/v1/task/'

        data = {
            'lead_id': lead_id,
            'text': 'Email new signup immediately',
            'is_complete': False
        }

        r = requests.post(url, auth=auth, data=json.dumps(data))

        if r.status_code != 200:
            raise Exception("Couldn't create task")

    def save(self, *args, **kwargs):
        created = False if self.pk else True

        super(Signup, self).save(*args, **kwargs)

        if created:
            tasks.process_signup_notification(self.pk)


class TooManyEmbedsExceptions(Exception):
    pass


class EmbedManager(models.Manager):

    def get_current(self):
        try:
            return self.all()[0]
        except IndexError:
            return


class Embed(BaseModel):
    publication = models.ForeignKey(Publication)

    objects = EmbedManager()

    def save(self, *args, **kwargs):
        if not self.pk and Embed.objects.all().count() == 1:
            raise TooManyEmbedsExceptions()

        return super(Embed, self).save(*args, **kwargs)
