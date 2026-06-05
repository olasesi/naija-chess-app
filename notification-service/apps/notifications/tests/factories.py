import factory
from apps.notifications.models import Notification, PushDevice


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    recipient_id = "user-123"
    type = Notification.Type.SYSTEM
    title = "Test Notification"
    body = "This is a test notification"


class PushDeviceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PushDevice

    user_id = "user-123"
    token = factory.Sequence(lambda n: f"device-token-{n}")
    platform = PushDevice.Platform.WEB
