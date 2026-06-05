from django.urls import path
from .views import LeaderboardView

urlpatterns = [
    path("leaderboard/<str:timeControl>", LeaderboardView.as_view(), name="leaderboard-detail"),
    path("leaderboard", LeaderboardView.as_view(), name="leaderboard-list"),
]
