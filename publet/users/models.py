import uuid
from hashlib import sha1
import hmac
import re
from datetime import datetime

from django.db import models
from django.conf import settings
from django.core import validators
from django.core.mail import send_mail
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, Group, Permission
)
from publet.groups.models import GroupMember, Group as PubletGroup
from publet.projects.models import Publication, Article
from django.contrib import auth

ACCOUNT_TYPES = (
    ('B', 'Basic'),
    ('P', 'Pro'),
    ('R', 'Reader'),
    ('T', 'Trial'),
    ('F', 'Free'),
)


class PubletUserManager(BaseUserManager):

    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            username=username
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(username, email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class PubletUser(AbstractBaseUser):
    """
    This is set up in a way to mirror the built-in ``User`` model
    """
    username = models.CharField(
        max_length=30, unique=True, validators=[
            validators.RegexValidator(re.compile('^[\w.@+-]+$'),
                                      'Enter a valid username.', 'invalid')
        ])
    # password is in the abstract class
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=datetime.utcnow)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    # PermissionsMixin overrides
    # NOTE: We can't simply inherit from the PermissionsMixin model because
    # Django doesn't support field hiding.
    # https://docs.djangoproject.com/en/1.7/topics/db/models/#field-name-hiding-is-not-permitted
    # It's important that we set the `related_query_name` argument in addition
    # to the `related_name` one.  This is used by the auth backend for reverse
    # queries in the Django admin.
    is_superuser = models.BooleanField(default=False)
    groups = models.ManyToManyField(
        Group, blank=True, related_name="publetuser_set",
        related_query_name="publetuser")
    user_permissions = models.ManyToManyField(
        Permission, blank=True, related_name="publetuser_set",
        related_query_name="publetuser")

    # Old UserProfile fields here
    job_title = models.CharField(max_length=255, blank=True, null=True)
    twitter = models.CharField(max_length=100, blank=True, null=True)
    facebook = models.CharField(max_length=255, blank=True, null=True)
    linkedin = models.CharField(max_length=255, blank=True, null=True)
    googleplus = models.CharField(max_length=255, blank=True, null=True)

    account_type = models.CharField(max_length=1, choices=ACCOUNT_TYPES,
                                    default='R')
    stripe_id = models.CharField(max_length=100, null=True, blank=True)

    objects = PubletUserManager()

    REQUIRED_FIELDS = ['email']
    USERNAME_FIELD = 'username'

    def get_full_name(self):
        if self.first_name or self.last_name:
            return '{} {}'.format(self.first_name, self.last_name)

    def get_short_name(self):
        return self.first_name

    def get_name(self):
        return self.get_full_name() or self.username

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])

    # UserProfile methods
    def get_groups(self):
        return PubletGroup.objects.filter(
            groupmember__in=GroupMember.objects.filter(user=self)
        ).order_by('name')

    def get_publications(self):
        return Publication.objects.filter(
            group__in=self.get_groups()
        ).order_by('name')

    def get_articles(self):
        return Article.objects.filter(
            publication__group__in=self.get_groups()
        ).order_by('name')

    @property
    def groups_count(self):
        return self.get_groups().count()

    @property
    def is_author(self):
        return not self.is_reader

    @property
    def is_basic(self):
        return self.account_type == 'B'

    @property
    def is_pro(self):
        if self.account_type == 'T':
            # TODO: In the future, we'll have rules for trial users
            return True
        return self.account_type == 'P'

    @property
    def is_reader(self):
        return self.account_type == 'R'

    @property
    def is_free(self):
        return self.account_type == 'F'

    @property
    def is_trial(self):
        return self.account_type == 'T'

    def can_create_publication_type(self, publication_type):
        if self.is_basic:
            if publication_type.name != 'Identity':
                return False

        return True

    # PermissionsMixin methods
    def get_group_permissions(self, obj=None):
        # From django.contrib.auth.models.PermissionsMixin
        permissions = set()
        for backend in auth.get_backends():
            if hasattr(backend, "get_group_permissions"):
                permissions.update(backend.get_group_permissions(self, obj))
        return permissions

    def get_all_permissions(self, obj=None):
        # From django.contrib.auth.models.PermissionsMixin
        return auth._user_get_all_permissions(self, obj)

    def has_perm(self, perm, obj=None):
        # From django.contrib.auth.models.PermissionsMixin
        if self.is_active and self.is_superuser:
            return True

        return auth._user_has_perm(self, perm, obj)

    def has_perms(self, perm_list, obj=None):
        # From django.contrib.auth.models.PermissionsMixin
        for perm in perm_list:
            if not self.has_perm(perm, obj):
                return False
        return True

    def has_module_perms(self, app_label):
        # From django.contrib.auth.models.PermissionsMixin
        if self.is_active and self.is_superuser:
            return True

        return auth._user_has_module_perms(self, app_label)

    @property
    def as_json(self):
        return {
            'id': self.pk,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'job_title': self.job_title,
            'twitter': self.twitter,
            'facebook': self.facebook,
            'googleplus': self.googleplus,
            'linkedin': self.linkedin,
            'groups': [g.json() for g in self.get_groups()]
        }


class PubletApiKey(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name='publet_api_key')
    key = models.CharField(max_length=128, blank=True, default='',
                           db_index=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    def generate_key(self):
        # Get a random UUID.
        new_uuid = uuid.uuid4()
        # Hmac that beast.
        return hmac.new(new_uuid.bytes, digestmod=sha1).hexdigest()

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()

        return super(PubletApiKey, self).save(*args, **kwargs)


def create_api_key(sender, **kwargs):
    """
    A signal for hooking up automatic ``ApiKey`` creation.
    """
    if kwargs.get('created') is True:
        PubletApiKey.objects.create(user=kwargs.get('instance'))


# Automatically create an API key for the user.
models.signals.post_save.connect(create_api_key, sender=PubletUser)
