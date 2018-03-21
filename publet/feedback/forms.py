from django import forms
from models import Feedback


class IntegrationFeedbackForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea)

    def save(self, user):
        message = self.cleaned_data['message']
        Feedback.objects.create_feedback(1, message, user=user)
