from django.contrib import admin
from .models import CachedLeaderboard


@admin.register(CachedLeaderboard)
class CachedLeaderboardAdmin(admin.ModelAdmin):
    list_display = ["timeControl", "totalPlayers", "updatedAt"]
    list_filter = ["timeControl"]
