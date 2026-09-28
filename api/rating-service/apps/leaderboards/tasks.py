from celery import shared_task
from django.core.cache import cache
from apps.ratings.models import PlayerRating
from .models import CachedLeaderboard, TimeControl


@shared_task
def refresh_leaderboard(time_control: str = None):
    """Refresh cached leaderboard for a given time control (or all)."""
    controls = [time_control] if time_control else [tc[0] for tc in TimeControl.choices]

    for tc in controls:
        top_players = (
            PlayerRating.objects
            .filter(timeControl=tc)
            .exclude(gamesPlayed=0)
            .order_by("-rating")[:100]
        )

        rankings = []
        for rank, player in enumerate(top_players, 1):
            rankings.append({
                "rank": rank,
                "userId": player.userId,
                "rating": round(player.rating),
                "rd": round(player.ratingDeviation),
                "gamesPlayed": player.gamesPlayed,
                "provisional": player.provisional,
                "lastGameAt": player.lastGameAt.isoformat() if player.lastGameAt else None,
            })

        CachedLeaderboard.objects.update_or_create(
            timeControl=tc,
            defaults={
                "rankings": rankings,
                "totalPlayers": PlayerRating.objects.filter(timeControl=tc).exclude(gamesPlayed=0).count(),
            },
        )

        # Also cache in Redis for fast access
        cache.set(f"leaderboard:{tc}", rankings, timeout=300)  # 5 min
