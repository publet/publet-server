import logging

from django.utils.timezone import now
from django.template.loader import render_to_string
from django.db import models
from django.conf import settings

import stripe

from publet.groups.models import Group
from publet.projects.models import Publication

logger = logging.getLogger(__name__)
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
TESTING = getattr(settings, 'TESTING', None)
DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
HOST = getattr(settings, 'HOST', None)
User = settings.USER_MODEL


class Purchase(models.Model):

    PURCHASE_TYPES = (
        ('publication', 'Publication'),
        ('subscription', 'Subscription'),
    )

    user = models.ForeignKey(User)
    group = models.ForeignKey(Group, blank=True, null=True)
    publication = models.ForeignKey(Publication, blank=True, null=True)

    purchase_type = models.CharField(max_length=50, choices=PURCHASE_TYPES)
    stripe_id = models.CharField(max_length=100, default='')

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def save(self, *args, **kwargs):
        created = False if self.pk else True
        skip_receipt = kwargs.pop('skip_receipt', None)

        super(Purchase, self).save(*args, **kwargs)

        if skip_receipt:
            return

        if created:
            from publet.utils.models import UserAccountRequest
            uar = UserAccountRequest.objects.filter(user=self.user)

            if uar:
                return

            context = {
                'user': self.user,
                'publication': self.publication,
                'type': self.purchase_type,
                'host': HOST
            }
            message = render_to_string('purchase_receipt_email.txt', context)
            self.user.email_user('Purchase receipt',
                                 message, DEFAULT_FROM_EMAIL)


class BaseCoupon(models.Model):
    is_active = models.BooleanField(default=False)
    code = models.CharField(max_length=20, unique=True)
    purchases = models.ManyToManyField(Purchase, blank=True)
    expires = models.DateTimeField(null=True, blank=True)
    new_price = models.IntegerField(null=True, blank=True)  # In pennies

    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.code

    @property
    def purchase_count(self):
        """
        Number of purchases made with this coupon
        """
        return self.purchases.count()

    @property
    def is_expired(self):
        if not self.expires:
            return False

        return now() > self.expires


class GroupSubscriptionCoupon(BaseCoupon):
    group = models.ForeignKey(Group)

    @property
    def plan_id(self):
        return 'group-coupon-{}'.format(self.pk)

    def save(self, *args, **kwargs):
        created = True if not self.pk else False

        super(GroupSubscriptionCoupon, self).save(*args, **kwargs)

        if created and not TESTING:

            name = 'Group subscription plan for {} with a coupon'.format(
                self.group.name)

            stripe.Plan.create(
                amount=self.new_price,
                interval='month',
                name=name,
                currency='usd',
                id=self.plan_id)

            logger.info('stripe plan created')


class PublicationCoupon(BaseCoupon):
    publication = models.ForeignKey(Publication)
