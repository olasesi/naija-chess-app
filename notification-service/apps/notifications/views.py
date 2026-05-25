from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, mixins
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db.models import Q
from django.conf import settings

from .models import Notification, PushDevice
from .serializers import (
    NotificationSerializer,
    MarkReadSerializer,
    PushDeviceSerializer,
    InternalSendSerializer,
)


class NotificationViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.filter(recipient_id=self.request.user.id)
        read_filter = self.request.query_params.get("read")
        if read_filter == "true":
            qs = qs.filter(read_at__isnull=False)
        elif read_filter == "false":
            qs = qs.filter(read_at__isnull=True)
        return qs

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = Notification.objects.filter(
            recipient_id=request.user.id, read_at__isnull=True
        ).count()
        return Response({"count": count})

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        notification = self.get_object()
        if notification.recipient_id != request.user.id:
            return Response({"success": False, "message": "Not your notification"}, status=403)
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
        return Response({"success": True, "message": "Marked as read"})

    @action(detail=False, methods=["post"])
    def read_all(self, request):
        serializer = MarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data.get("notification_ids")
        qs = Notification.objects.filter(recipient_id=request.user.id, read_at__isnull=True)
        if ids:
            qs = qs.filter(id__in=ids)
        updated = qs.update(read_at=timezone.now())
        return Response({"success": True, "message": f"{updated} notifications marked as read"})


class PushDeviceViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, GenericViewSet):
    serializer_class = PushDeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PushDevice.objects.filter(user_id=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id)


class InternalNotificationViewSet(mixins.CreateModelMixin, GenericViewSet):
    """
    Internal endpoint for other microservices to send notifications.
    """
    serializer_class = InternalSendSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        notification = Notification.objects.create(
            recipient_id=data["recipient_id"],
            type=data["type"],
            title=data["title"],
            body=data["body"],
            data=data.get("data", {}),
        )

        # Trigger push notification async (lazy import for test isolation)
        if not settings.CELERY_TASK_ALWAYS_EAGER:
            from .tasks import send_push_notification
            send_push_notification.delay(
                user_id=data["recipient_id"],
                title=data["title"],
                body=data["body"],
                data=data.get("data", {}),
            )

        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_201_CREATED,
        )
