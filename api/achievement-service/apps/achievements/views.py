import uuid

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .engine import handle_event
from .models import Achievement, UserAchievement, UserXP
from .serializers import (
    AchievementSerializer,
    EventInputSerializer,
    UserAchievementSerializer,
    UserXPSerializer,
)


class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """Achievement catalog. List/detail include the current user's status."""

    queryset = Achievement.objects.filter(is_active=True)
    serializer_class = AchievementSerializer
    lookup_field = "code"
    filterset_fields = ["category"]

    @action(detail=False, methods=["GET"])
    def mine(self, request):
        """The current user's unlocked achievements and in-progress ones."""
        records = UserAchievement.objects.filter(user_id=request.user.id).select_related(
            "achievement"
        )
        unlocked = records.filter(unlocked_at__isnull=False)
        in_progress = records.filter(unlocked_at__isnull=True, progress__gt=0)

        return Response(
            {
                "unlocked_count": unlocked.count(),
                "in_progress_count": in_progress.count(),
                "unlocked": UserAchievementSerializer(unlocked, many=True, context={"request": request}).data,
                "in_progress": UserAchievementSerializer(
                    in_progress, many=True, context={"request": request}
                ).data,
            }
        )

    @action(detail=False, methods=["GET"])
    def xp(self, request):
        """The current user's XP and level."""
        record, created = UserXP.objects.get_or_create(user_id=request.user.id)
        return Response(UserXPSerializer(record).data)

    @action(detail=False, methods=["POST"])
    def event(self, request):
        """
        Record a lifecycle event (game won, puzzle solved, streak, etc.)
        and evaluate unlocks. Called by other services through the gateway.
        """
        serializer = EventInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = handle_event(
            request.user.id,
            {
                "type": serializer.validated_data["type"],
                "value": serializer.validated_data.get("value", 1),
                "xp": request.data.get("xp"),
            },
        )
        return Response(result, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["GET"])
    def leaderboard(self, request):
        """Top users by total XP."""
        records = (
            UserXP.objects.order_by("-total_xp", "updated_at")
            .values("user_id", "total_xp", "level")[:50]
        )
        return Response({"results": list(records)})