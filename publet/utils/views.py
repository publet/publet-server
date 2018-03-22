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
import json

from annoying.decorators import render_to

from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site, RequestSite

from registration.backends.default.views import RegistrationView
from registration.models import RegistrationProfile
from registration import signals

from publet.utils.forms import (
    PubletRegistrationForm, EmailChangeForm, ProfileForm, SignupForm
)
from publet.utils.models import (
    UserAccountRequest, Invite, Welcome, BulkUserUpload, Embed, Signup
)
from publet.groups.models import Group


INSTALLATION = getattr(settings, 'INSTALLATION', None)


class PubletRegistrationView(RegistrationView):
    """
    Custom registration view that uses our custom form.
    """
    form_class = PubletRegistrationForm

    def register(self, request, form):
        cleaned_data = form.cleaned_data
        username, email, password = (cleaned_data['username'],
                                     cleaned_data['email'],
                                     cleaned_data['password1'])
        if Site._meta.installed:
            site = Site.objects.get_current()
        else:
            site = RequestSite(request)

        new_user = RegistrationProfile.objects.create_inactive_user(
            site, email=email, password=password, username=username)

        new_user.account_type = 'F'

        # try:
        #     invite = Invite.objects.get(code=author_code)
        # except Invite.DoesNotExist:
        #     invite = None

        # if invite and invite.active and not invite.is_redeemed:
        #     new_user.account_type = invite.user_type
        #     new_user.save()

        #     invite.user = new_user
        #     invite.save()

        #     invite.add_purchases()
        #     invite.add_groups()

        new_user.save()
        Welcome.objects.run_for_user(new_user)

        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=request)

        return new_user


@login_required
def change_account_type(request):
    request.user.account_type = 'R'
    request.user.save()

    return redirect('/')


@render_to('activate.html')
def activate(request, uuid):
    uar = get_object_or_404(UserAccountRequest, uuid=uuid)

    if uar.user:
        raise Http404

    if request.method == 'POST':
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        password2 = request.POST.get('password2', None)

        if not username or not password or not password2:
            return dict(error='All fields are required')

        if password != password2:
            return dict(error="Passwords don't match")

        user, created = get_user_model().objects.get_or_create(
            username=username)
        upload = uar.upload

        if upload.created_via_admin:
            account_type = upload.account_type
        else:
            account_type = 'B'

        if created:
            user.first_name = uar.first
            user.last_name = uar.last
            user.email = uar.email
            user.set_password(password)
            user.save()

            user.account_type = account_type
            user.save()

            uar.user = user
            uar.save()
            uar.add_purchases()
            uar.add_groups()

            Welcome.objects.run_for_user(user)

            messages.info(request, 'Activated! Now you can log in to see your '
                                   'publications.')

            return redirect('auth_login')
        else:
            return dict(error='Username is taken.  Try again please.')

    return {}


@csrf_exempt
@login_required
def bulk_invite(request):
    if request.method != 'POST':
        raise Http404

    auth = request.META.get('HTTP_AUTHORIZATION', None)
    api_key = auth.split(' ')[1].split(':')[1]

    if request.user.publet_api_key.key != api_key:
        raise Http404

    data = json.loads(request.body)
    group = Group.objects.get(pk=data['group'])

    b = BulkUserUpload(csv_data=data['users'], name=group.name,
                       account_type='B', group_role=data['type'])
    b.save(skip_creation=True)
    b.groups.add(group)
    b.save()

    b.notify()

    return HttpResponse('')


@login_required
def impersonate(request):
    if INSTALLATION not in ['dev', 'staging']:
        raise Http404

    if not request.user.is_superuser:
        raise Http404

    if request.method != 'POST':
        raise Http404

    user = request.POST.get('user', None)

    if not user:
        raise Http404

    user = get_object_or_404(get_user_model(), pk=int(user))

    request.session['_impersonate'] = user.pk

    return redirect('/')


@login_required
@render_to('email_change_form.html')
def change_email(request):
    if request.method == 'POST':
        form = EmailChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            messages.info(request, 'Saved!')
            form.save()
    else:
        form = EmailChangeForm(instance=request.user)

    return {
        'form': form
    }


@login_required
@render_to('profile.html')
def profile(request):

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.info(request, 'Saved')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)

    return {
        'form': form
    }


@render_to('signup-form.html')
def signup_form(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('http://publet.com/thankyou.html')
    else:
        form = SignupForm()

    return {
        'form': form
    }


@csrf_exempt
def publet_sign_up_handler(request):
    """
    Registrations from publet.com
    """
    if request.method not in ['POST', 'OPTIONS']:
        raise Http404

    origin = request.META.get('HTTP_ORIGIN', '*')

    if request.method == 'OPTIONS':
        response = HttpResponse('POST')
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Allow-Methods'] = 'POST'
        response['Allow'] = 'POST'
        return response

    email = request.POST.get('email', None)

    if not email:
        raise Http404

    Signup.objects.create(email=email, first_name_and_last_name=email,
                          organization=email)

    response = HttpResponse('')
    response['Access-Control-Allow-Origin'] = origin
    return response


@render_to('embed-test.html')
def embed_test(request):
    embed = Embed.objects.get_current()
    return {
        'embed_code': embed.publication.get_embed_code()
    }
