from annoying.decorators import render_to
from annoying.functions import get_object_or_None
from django.conf import settings
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from publet.groups.models import Group
from publet.payments.models import (
    Purchase, PublicationCoupon, GroupSubscriptionCoupon
)
from publet.projects.models import Publication

import stripe


@login_required
def downgrade(request):

    stripe.api_key = settings.STRIPE_SECRET_KEY
    cu = stripe.Customer.retrieve(request.user.stripe_id)
    cu.cancel_subscription()

    # TODO: This should be a POST, so someone can't be tricked into
    # downgrading.
    request.user.account_type = 'B'
    request.user.stripe_id = None
    request.user.save()

    return redirect('payments-upgrade')


@login_required
@render_to('payments/preorder.html')
def preorder(request, group_slug, publication_slug):

    group = get_object_or_404(Group, slug=group_slug)
    publication = get_object_or_404(Publication, slug=publication_slug,
                                    group=group)

    already_purchased = get_object_or_None(Purchase, publication=publication,
                                           user=request.user)

    data = {
        'already_purchased': already_purchased,
        'publication': publication,
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY
    }

    if publication.status != 'preorder':
        return redirect('preview-publication-html',
                        group_slug=publication.group.slug,
                        publication_slug=publication.slug)

    if request.method == 'POST':

        token = request.POST['stripeToken']
        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            charge = stripe.Charge.create(

                # TODO: this is really dumb. Force publication price to cents
                # somewhere else.
                amount=str(publication.price).replace('.', ''),

                currency="usd",
                card=token,
                description="{} preordering {} ({})".format(request.user.email,
                                                            publication.name,
                                                            publication.id)
            )

            purchase = Purchase(user=request.user, publication=publication,
                                purchase_type='publication',
                                stripe_id=charge.id)
            purchase.save()

            data['already_purchased'] = purchase
            data['purchase_successful'] = True
        except stripe.CardError:
            data['errors'] = 'The card has been declined'
            data['purchase_successful'] = False

    return data


@render_to('payments/purchase.html')
def purchase(request, group_slug, publication_slug):
    user = request.user
    is_anon = user.is_anonymous()

    group = get_object_or_404(Group, slug=group_slug)
    publication = get_object_or_404(Publication, slug=publication_slug,
                                    group=group)

    if is_anon:
        already_purchased = None
    else:
        already_purchased = get_object_or_None(Purchase,
                                               publication=publication,
                                               user=user)

    if already_purchased:
        return redirect('preview-publication-html',
                        group_slug=publication.group.slug,
                        publication_slug=publication.slug)

    coupon = request.GET.get('coupon', None)
    price = publication.price

    if coupon:
        coupon = get_object_or_None(PublicationCoupon, code=coupon)

        if coupon and coupon.is_active and not coupon.is_expired:
            price = coupon.new_price

    data = {
        'already_purchased': already_purchased,
        'publication': publication,
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY,
        'price': price,
        'is_anon': is_anon
    }

    if publication.status in ['hidden', 'preorder']:
        return redirect('preview-publication-html',
                        group_slug=publication.group.slug,
                        publication_slug=publication.slug)

    if request.method == 'POST':

        token = request.POST['stripeToken']
        stripe.api_key = settings.STRIPE_SECRET_KEY

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if is_anon:

            data['username'] = username
            data['email'] = email

            if password != password2:
                data['errors'] = "Passwords don't match"
                return data

            if not username:
                data['errors'] = "Username required"
                return data

            try:
                user = get_user_model().objects.create(email=email,
                                                       username=username)
                user.set_password(password)
                user.save()
            except:
                data['errors'] = "User exists"
                return data

            user = authenticate(username=username, password=password)
            login(request, user)

        try:
            charge = stripe.Charge.create(

                # TODO: this is really dumb. Force publication price to cents
                # somewhere else.
                amount=str(publication.price).replace('.', ''),

                currency="usd",
                card=token,
                description="{} purchasing {} ({})".format(user.email,
                                                           publication.name,
                                                           publication.id)
            )

            purchase = Purchase(user=user, publication=publication,
                                purchase_type='publication',
                                stripe_id=charge.id)
            purchase.save()

            data['already_purchased'] = purchase
            data['purchase_successful'] = True
        except stripe.CardError:
            data['errors'] = 'The card has been declined'
            data['purchase_successful'] = False

    return data


@login_required
@render_to('payments/upgrade.html')
def upgrade(request):

    data = {
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY
    }

    if request.method == 'POST':

        token = request.POST['stripeToken']
        stripe.api_key = settings.STRIPE_SECRET_KEY

        plan = 'publet-pro'

        customer = stripe.Customer.create(
            card=token,
            plan=plan,
            email=request.user.email
        )

        request.user.account_type = 'P'
        request.user.stripe_id = customer.id
        request.user.save()

        data['upgrade_successful'] = True

    return data


@login_required
@render_to('payments/subscribe.html')
def subscribe(request, group_slug):
    group = get_object_or_404(Group, slug=group_slug)

    coupon = (request.GET.get('coupon', None) or
              request.POST.get('coupon', None))

    price = group.price
    plan_id = group.plan_id

    already_subscribed = group.is_user_subscribed(request.user)

    data = {
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY,
        'group': group,
        'coupon': False,
        'already_subscribed': already_subscribed
    }

    if coupon:
        coupon = get_object_or_None(GroupSubscriptionCoupon, code=coupon)

        if coupon and coupon.is_active and not coupon.is_expired:
            price = coupon.new_price
            plan_id = coupon.plan_id
            data['coupon'] = coupon.code

    data['price'] = price

    if request.method == 'POST' and not already_subscribed:

        token = request.POST['stripeToken']
        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            charge = stripe.Customer.create(
                card=token,
                plan=plan_id,
                email=request.user.email
            )

            purchase = Purchase(user=request.user, group=group,
                                purchase_type='subscription',
                                stripe_id=charge.id)
            purchase.save()

            data['already_purchased'] = purchase
            data['purchase_successful'] = True
        except stripe.CardError:
            data['errors'] = 'The card has been declined'
            data['purchase_successful'] = False

    return data


@login_required
@render_to('payments/confirm-unsubscribe.html')
def unsubscribe(request, group_slug):
    group = get_object_or_404(Group, slug=group_slug)
    purchase = get_object_or_404(Purchase, group=group, user=request.user,
                                 purchase_type='subscription')

    if request.method == 'POST':

        purchase.delete()

        return redirect('profile-detail', profile_slug=group_slug)

    return {
        'group': group
    }
