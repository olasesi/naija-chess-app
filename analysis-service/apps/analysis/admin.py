from django.contrib import admin
from .models import GameAnalysis, CachedPosition


@admin.register(GameAnalysis)
class GameAnalysisAdmin(admin.ModelAdmin):
    list_display = ["gameId", "status", "depth", "totalMoves", "eco", "opening", "createdAt", "completedAt"]
    list_filter = ["status", "depth"]
    search_fields = ["gameId", "eco", "opening"]
    date_hierarchy = "createdAt"


@admin.register(CachedPosition)
class CachedPositionAdmin(admin.ModelAdmin):
    list_display = ["fen_short", "depth", "score", "mate", "bestMove", "evaluatedAt"]

    def fen_short(self, obj):
        return obj.fen[:40] + "..."
    fen_short.short_description = "FEN"
