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
