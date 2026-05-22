from django.contrib import admin
from .models import UserStats


@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    list_display = [
        "userId", "gamesPlayed", "wins", "losses", "draws",
        "bulletRating", "blitzRating", "rapidRating", "classicalRating",
    ]
    list_filter = ["bulletRating", "blitzRating"]
    search_fields = ["userId"]
    readonly_fields = [f.name for f in UserStats._meta.fields if f.name != "id"]
