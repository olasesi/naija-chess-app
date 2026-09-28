from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsOwner, IsAdmin
from .models import UserStats
from .serializers import UserStatsSerializer, RecordGameResultSerializer
from .elo import calculate_rating


class StatsDetailView(APIView):
    permission_classes = [IsOwner | IsAdmin]

    def get_object(self, userId):
        stats, created = UserStats.objects.get_or_create(userId=userId)
        return stats

    def get(self, request, userId=None):
        userId = userId or getattr(request.user, "id", None)
        stats = self.get_object(userId)
        serializer = UserStatsSerializer(stats)
        return Response(serializer.data)


class RecordGameResultView(APIView):
    permission_classes = [IsOwner]

    def post(self, request):
        userId = getattr(request.user, "id", None)
        serializer = RecordGameResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        stats, _ = UserStats.objects.get_or_create(userId=userId)

        result = serializer.validated_data["result"]
        timeControl = serializer.validated_data["timeControl"]
        opponentRating = serializer.validated_data["opponentRating"]

        # Update counts
        stats.gamesPlayed += 1
        if result == "win":
            stats.wins += 1
            stats.winStreak += 1
            if stats.winStreak > stats.bestWinStreak:
                stats.bestWinStreak = stats.winStreak
        elif result == "loss":
            stats.losses += 1
            stats.winStreak = 0
        else:
            stats.draws += 1

        # Update rating
        score = 1.0 if result == "win" else (0.5 if result == "draw" else 0.0)
        rating_field = f"{timeControl}Rating"
        current_rating = getattr(stats, rating_field)
        new_rating = calculate_rating(current_rating, opponentRating, score)
        setattr(stats, rating_field, new_rating)

        stats.save()

        return Response(
            UserStatsSerializer(stats).data,
            status=status.HTTP_200_OK,
        )
