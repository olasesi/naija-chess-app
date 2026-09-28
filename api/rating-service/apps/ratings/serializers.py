from rest_framework import serializers
from .models import PlayerRating, RatingHistory


class PlayerRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerRating
        fields = [
            "userId", "timeControl",
            "rating", "ratingDeviation", "volatility",
            "gamesPlayed", "wins", "losses", "draws",
            "provisional", "lastGameAt", "createdAt", "updatedAt",
        ]
        read_only_fields = [f.name for f in PlayerRating._meta.fields if f.name != "id"]


class RatingHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RatingHistory
        fields = "__all__"
        read_only_fields = [f.name for f in RatingHistory._meta.fields]


class UpdateRatingSerializer(serializers.Serializer):
    gameId = serializers.CharField(max_length=36)
    whiteUserId = serializers.CharField(max_length=36)
    blackUserId = serializers.CharField(max_length=36)
    result = serializers.ChoiceField(choices=["1-0", "0-1", "1/2-1/2"])
    timeControl = serializers.ChoiceField(choices=["bullet", "blitz", "rapid", "classical", "puzzle"])
    playedAt = serializers.DateTimeField()
