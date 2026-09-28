from django.contrib import admin

from .models import UserBlock


@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    list_display = ["userId", "blockedId", "type", "reason", "createdAt"]
    list_filter = ["type"]
    search_fields = ["userId", "blockedId"]
    date_hierarchy = "createdAt"