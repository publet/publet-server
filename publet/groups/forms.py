from django import forms
from publet.groups.models import GroupHub


class GroupHubForm(forms.ModelForm):

    class Meta:
        model = GroupHub
        fields = ('name', 'publications',)

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group')
        super(GroupHubForm, self).__init__(*args, **kwargs)
        self.fields['publications'].queryset = \
            self.group.publication_set.filter(status='live')
