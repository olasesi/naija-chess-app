from django.contrib import admin
from .models import Friend


@admin.register(Friend)
class FriendAdmin(admin.ModelAdmin):
    list_display = ["userId", "friendId", "status", "createdAt"]
    list_filter = ["status"]
    search_fields = ["userId", "friendId"]
    date_hierarchy = "createdAt"
