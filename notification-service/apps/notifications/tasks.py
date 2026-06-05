from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_push_notification(self, user_id, title, body, data=None):
    """Send push notification to all active devices for a user."""
    from .models import PushDevice

    devices = PushDevice.objects.filter(user_id=user_id, is_active=True)
    if not devices.exists():
        logger.info(f"No active devices for user {user_id}")
        return

    for device in devices:
        try:
            if device.token:
                # Placeholder: integrate with FCM/APNS/WebPush here
                # For Firebase:
                # from pyfcm import FCMNotification
                # push = FCMNotification(api_key=settings.FCM_SERVER_KEY)
                # push.notify_single_device(
                #     registration_id=device.token,
                #     message_title=title,
                #     message_body=body,
                #     data_message=data or {},
                # )
                logger.info(f"Push sent to device {device.id} for user {user_id}")
        except Exception as exc:
            logger.error(f"Push failed for device {device.id}: {exc}")
            if device.is_active:
                device.is_active = False
                device.save(update_fields=["is_active"])


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_email_notification(self, recipient_email, subject, message):
    """Send email notification."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info(f"Email sent to {recipient_email}: {subject}")
    except Exception as exc:
        logger.error(f"Email failed to {recipient_email}: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_to_user(self, user_id, notification_type, title, body, data=None):
    """High-level task: create notification + push + optionally email."""
    from .models import Notification

    notification = Notification.objects.create(
        recipient_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        data=data or {},
    )

    send_push_notification.delay(
        user_id=user_id,
        title=title,
        body=body,
        data=data,
    )

    return notification.id
