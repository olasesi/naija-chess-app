from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["userId", "displayName", "country", "title", "createdAt"]
    list_filter = ["country", "title"]
    search_fields = ["userId", "displayName"]
    readonly_fields = ["userId", "createdAt", "updatedAt"]
    date_hierarchy = "createdAt"
