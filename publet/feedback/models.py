import json
import requests
import logging
from django.conf import settings
from django.db import models
from publet.common.models import BaseModel
from tasks import send_feedback_to_slack

logger = logging.getLogger(__name__)
SLACK_WEBHOOK_FEEDBACK = getattr(settings, 'SLACK_WEBHOOK_FEEDBACK', None)
INSTALLATION = getattr(settings, 'INSTALLATION', None)


class FeedbackManager(models.Manager):

    def create_feedback(self, type, message, user=None):
        f = Feedback(type=type, message=message, created_by=user)
        f.save()
        send_feedback_to_slack.delay(f.pk)
        return f


class Feedback(BaseModel):
    TYPES = (
        (1, 'New integration',),
        (2, 'I wish',),
    )

    type = models.IntegerField(choices=TYPES)
    message = models.TextField()

    objects = FeedbackManager()

    @property
    def slack_username(self):
        return '[{}] New feedback - {}'.format(INSTALLATION,
                                               self.get_type_display())

    def send_slack_message(self):
        if not SLACK_WEBHOOK_FEEDBACK:
            logger.error('slack webhook not configured')
            return

        author = self.created_by.get_full_name() + ' ' + self.created_by.email
        full_text = self.message + '\n\n' + author

        data = {
            'username': self.slack_username,
            'attachments': [{
                'fields': [{
                    'title': self.get_type_display(),
                    'value': full_text,
                    'short': False
                }]
            }]
        }

        payload = json.dumps(data)
        requests.post(SLACK_WEBHOOK_FEEDBACK, data=payload)
