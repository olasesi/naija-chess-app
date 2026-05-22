from rest_framework import serializers
from .models import UserStats


class UserStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStats
        fields = [
            "userId", "gamesPlayed", "wins", "losses", "draws",
            "winStreak", "bestWinStreak",
            "bulletRating", "blitzRating", "rapidRating", "classicalRating",
            "puzzleRating", "puzzleRatingMax",
            "createdAt", "updatedAt",
        ]
        read_only_fields = [
            field.name
            for field in UserStats._meta.fields
            if field.name != "userId"
        ]


class RecordGameResultSerializer(serializers.Serializer):
    result = serializers.ChoiceField(choices=["win", "loss", "draw"])
    timeControl = serializers.ChoiceField(
        choices=["bullet", "blitz", "rapid", "classical"]
    )
    opponentRating = serializers.IntegerField(min_value=0, max_value=4000)
