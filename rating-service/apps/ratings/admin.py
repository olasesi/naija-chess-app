from django.contrib import admin
from .models import PlayerRating, RatingHistory


@admin.register(PlayerRating)
class PlayerRatingAdmin(admin.ModelAdmin):
    list_display = ["userId", "timeControl", "rating", "ratingDeviation", "gamesPlayed", "provisional", "lastGameAt"]
    list_filter = ["timeControl", "provisional"]
    search_fields = ["userId"]


@admin.register(RatingHistory)
class RatingHistoryAdmin(admin.ModelAdmin):
    list_display = ["userId", "timeControl", "rating", "result", "gameId", "recordedAt"]
    list_filter = ["timeControl", "result"]
    search_fields = ["userId", "gameId"]
    date_hierarchy = "recordedAt"
