from django.contrib import admin
from .models import Notification, PushDevice


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient_id", "type", "title", "read_at", "created_at"]
    list_filter = ["type", "read_at", "created_at"]
    search_fields = ["recipient_id", "title", "body"]


@admin.register(PushDevice)
class PushDeviceAdmin(admin.ModelAdmin):
    list_display = ["user_id", "platform", "is_active", "created_at"]
    list_filter = ["platform", "is_active"]
    search_fields = ["user_id", "token"]
