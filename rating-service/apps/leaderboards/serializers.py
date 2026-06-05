from rest_framework import serializers
from .models import CachedLeaderboard


class LeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = CachedLeaderboard
        fields = ["timeControl", "rankings", "totalPlayers", "updatedAt"]
