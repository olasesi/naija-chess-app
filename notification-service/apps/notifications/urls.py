from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, PushDeviceViewSet, InternalNotificationViewSet

router = DefaultRouter()
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"devices", PushDeviceViewSet, basename="push-device")

urlpatterns = [
    path("", include(router.urls)),
    path("internal/send", InternalNotificationViewSet.as_view({"post": "create"}), name="internal-send"),
]
