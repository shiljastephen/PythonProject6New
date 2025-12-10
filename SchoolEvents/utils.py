from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .models import NotificationLog
import traceback

def send_notification(subject, template_name, context, to_emails, event=None, html=False):
    if isinstance(to_emails, str):
        to_emails = [to_emails]
    to_emails = [e for e in to_emails if e]
    if not to_emails:
        return False
    try:
        body = render_to_string(template_name, context)
        if html:
            msg = EmailMessage(subject=subject, body=body, from_email=settings.DEFAULT_FROM_EMAIL, to=to_emails)
            msg.content_subtype = "html"
            msg.send(fail_silently=False)
        else:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, to_emails, fail_silently=False)
        NotificationLog.objects.create(
            to_emails=",".join(to_emails),
            subject=subject,
            body=body,
            event=event,
            status='sent'
        )
        return True
    except Exception as e:
        NotificationLog.objects.create(
            to_emails=",".join(to_emails),
            subject=subject,
            body=str(e),
            event=event,
            status='failed',
            error=traceback.format_exc()
        )
        return False
