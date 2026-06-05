from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PlayerRating, RatingHistory
from .serializers import (
    PlayerRatingSerializer,
    RatingHistorySerializer,
    UpdateRatingSerializer,
)
from .tasks import process_game_result


class RatingDetailView(APIView):
    def get(self, request, userId=None):
        userId = userId or getattr(request.user, "id", None)
        time_control = request.query_params.get("timeControl")

        filters = {"userId": userId}
        if time_control:
            filters["timeControl"] = time_control

        ratings = PlayerRating.objects.filter(**filters)
        serializer = PlayerRatingSerializer(ratings, many=True)
        return Response(serializer.data)


class RatingHistoryView(APIView):
    def get(self, request, userId=None):
        userId = userId or getattr(request.user, "id", None)
        time_control = request.query_params.get("timeControl")
        limit = int(request.query_params.get("limit", 50))

        filters = {"userId": userId}
        if time_control:
            filters["timeControl"] = time_control

        history = RatingHistory.objects.filter(**filters)[:limit]
        serializer = RatingHistorySerializer(history, many=True)
        return Response(serializer.data)


class UpdateRatingView(APIView):
    permission_classes = []  # Internal service-to-service

    def post(self, request):
        serializer = UpdateRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Trigger async calculation
        result = process_game_result.delay(
            game_id=data["gameId"],
            white_user_id=data["whiteUserId"],
            black_user_id=data["blackUserId"],
            result=data["result"],
            time_control=data["timeControl"],
            played_at=data["playedAt"].isoformat(),
        )

        return Response(
            {"success": True, "message": "Rating update queued", "taskId": result.id},
            status=status.HTTP_202_ACCEPTED,
        )
