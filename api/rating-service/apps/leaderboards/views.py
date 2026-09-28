from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CachedLeaderboard, TimeControl
from .serializers import LeaderboardSerializer


class LeaderboardView(APIView):
    permission_classes = []  # Public

    def get(self, request, timeControl=None):
        time_control = timeControl or request.query_params.get("timeControl", "rapid")

        if time_control not in dict(TimeControl.choices):
            return Response(
                {"success": False, "message": f"Invalid time control: {time_control}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Try Redis cache first
        cached = cache.get(f"leaderboard:{time_control}")
        if cached:
            return Response({
                "timeControl": time_control,
                "rankings": cached,
                "totalPlayers": len(cached),
            })

        # Fallback to DB
        try:
            lb = CachedLeaderboard.objects.get(timeControl=time_control)
            serializer = LeaderboardSerializer(lb)
            return Response(serializer.data)
        except CachedLeaderboard.DoesNotExist:
            return Response({
                "timeControl": time_control,
                "rankings": [],
                "totalPlayers": 0,
            })
