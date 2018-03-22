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
from django.utils.translation import ugettext_lazy as _
from registration.forms import RegistrationForm
from django.contrib.auth import get_user_model
from django import forms

from publet.utils.models import Signup


class UniqueEmailMixin(object):

    def clean_email(self):
        """
        Validate that the supplied email address is unique for the
        site.
        """
        User = get_user_model()

        if User.objects.filter(email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError(_("This email address is already in "
                                          "use. Please supply a different "
                                          "email address."))
        return self.cleaned_data['email']


class PubletRegistrationForm(RegistrationForm, UniqueEmailMixin):
    """
    Subclass of ``RegistrationForm`` which enforces uniqueness of
    email addresses.
    """

    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.
        """
        existing = get_user_model().objects.filter(
            username__iexact=self.cleaned_data['username'])

        if existing.exists():
            raise forms.ValidationError(
                _("A user with that username already exists."))

        elif '@' in self.cleaned_data['username']:
            raise forms.ValidationError(_("Cannot have '@' in username."))
        elif '.' in self.cleaned_data['username']:
            raise forms.ValidationError(_("Cannot have '.' in username."))
        elif '+' in self.cleaned_data['username']:
            raise forms.ValidationError(_("Cannot have '+' in username."))

        else:
            return self.cleaned_data['username']


class EmailChangeForm(forms.ModelForm, UniqueEmailMixin):

    class Meta:
        fields = ('email',)
        model = get_user_model()


class ProfileForm(forms.ModelForm):

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email', 'job_title', 'twitter',
                  'facebook', 'linkedin', 'googleplus',)


class SignupForm(forms.ModelForm):

    class Meta:
        model = Signup
        exclude = ('created_by', 'created', 'modified',)
