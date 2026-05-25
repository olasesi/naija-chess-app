from django.core.management.base import BaseCommand
from apps.notifications.models import Notification
from apps.notifications.tasks import send_push_notification


class Command(BaseCommand):
    help = "Send a test notification to a user"

    def add_arguments(self, parser):
        parser.add_argument("user_id", type=str, help="Recipient user ID")
        parser.add_argument("--title", default="Test Notification", help="Notification title")
        parser.add_argument("--body", default="This is a test notification from the chess platform.", help="Notification body")
        parser.add_argument("--type", default="system", choices=[t.value for t in Notification.Type], help="Notification type")

    def handle(self, *args, **options):
        notification = Notification.objects.create(
            recipient_id=options["user_id"],
            type=options["type"],
            title=options["title"],
            body=options["body"],
        )

        send_push_notification.delay(
            options["user_id"],
            options["title"],
            options["body"],
        )

        self.stdout.write(self.style.SUCCESS(
            f"Notification {notification.id} sent to {options['user_id']}"
        ))
