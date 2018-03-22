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
from django import forms
from publet.groups.models import Group
from publet.projects.models import (
    PublicationSocialGateEntry, Publication,
    GateSubmission
)


class ChangeGroupForm(forms.Form):
    group = forms.ModelChoiceField(queryset=Group.objects.all(),
                                   empty_label='Empty')


class PublicationSocialGateEntryForm(forms.ModelForm):
    publication = forms.ModelChoiceField(queryset=None)

    class Meta:
        model = PublicationSocialGateEntry
        exclude = ('created_by',)

    def __init__(self, *args, **kwargs):
        super(PublicationSocialGateEntryForm, self).__init__(*args, **kwargs)
        self.fields['publication'].queryset = Publication.objects.all()

    def full_clean(self):
        self.data['publication'] = self.data['publication']['pk']

        try:
            data = json.loads(self.data['data'])
            self.data['anonymous_id'] = data.get('anonymous_id')
        except:
            pass

        return super(PublicationSocialGateEntryForm, self).full_clean()


class GenericGateForm(PublicationSocialGateEntryForm):

    class Meta:
        model = GateSubmission
        exclude = ('created_by',)
