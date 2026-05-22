from django.contrib import admin
from .models import UserPreference


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ["userId", "theme", "boardStyle", "pieceStyle", "soundEnabled"]
    list_filter = ["theme", "boardStyle", "pieceStyle"]
    search_fields = ["userId"]
