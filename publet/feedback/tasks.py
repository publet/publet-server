from django_rq import job


@job
def send_feedback_to_slack(feedback_id):
    from publet.feedback.models import Feedback
    f = Feedback.objects.get(pk=feedback_id)
    f.send_slack_message()
