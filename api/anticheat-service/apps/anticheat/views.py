from django.conf import settings
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .engine import evaluate_game
from .models import CheatSignal, GameFlag, UserSanction
from .serializers import (
    CheatSignalInputSerializer,
    CheatSignalSerializer,
    GameFlagSerializer,
    UserSanctionSerializer,
)


class SignalViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Telemetry input and query."""

    queryset = CheatSignal.objects.all()
    serializer_class = CheatSignalInputSerializer

    def get_queryset(self):
        qs = CheatSignal.objects.all()
        game_id = self.request.query_params.get("game_id")
        user_id = self.request.query_params.get("user_id")
        if game_id:
            qs = qs.filter(game_id=game_id)
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        signal = CheatSignal.objects.create(
            signal_type=serializer.validated_data["signal_type"],
            user_id=request.user.id,
            game_id=serializer.validated_data["game_id"],
            opponent_id=serializer.validated_data.get("opponent_id", ""),
            value=serializer.validated_data["value"],
            metadata=serializer.validated_data.get("metadata", {}),
        )
        data = CheatSignalSerializer(signal).data
        return Response(data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(CheatSignalSerializer(page, many=True).data)
        return Response(CheatSignalSerializer(qs, many=True).data)


class FlagViewSet(viewsets.ModelViewSet):
    """Flags, review triage, and resolution."""

    queryset = GameFlag.objects.all()
    serializer_class = GameFlagSerializer
    filterset_fields = ["status", "user_id"]

    def create(self, request):
        """Manually flag a single (user, game) pair."""
        game_id = request.data.get("game_id")
        user_id = request.data.get("user_id") or request.user.id
        if not game_id:
            return Response({"detail": "game_id required"}, status=status.HTTP_400_BAD_REQUEST)

        result = evaluate_game(user_id, game_id)
        flag, _ = GameFlag.objects.get_or_create(
            game_id=game_id,
            user_id=user_id,
            defaults={
                "opponent_id": request.data.get("opponent_id", ""),
                "suspicion_score": result["suspicion_score"],
                "reasons": result["reasons"],
            },
        )
        return Response(GameFlagSerializer(flag).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["POST"])
    def evaluate(self, request):
        """Score a game's signals; flag if the bar is crossed."""
        game_id = request.data.get("game_id")
        user_id = request.data.get("user_id") or request.user.id
        if not game_id:
            return Response({"detail": "game_id required"}, status=status.HTTP_400_BAD_REQUEST)

        result = evaluate_game(user_id, game_id)

        flag = None
        if result["flagged"]:
            flag, _ = GameFlag.objects.get_or_create(
                game_id=game_id,
                user_id=user_id,
                defaults={
                    "opponent_id": request.data.get("opponent_id", ""),
                    "suspicion_score": result["suspicion_score"],
                    "reasons": result["reasons"],
                },
            )
        result["flag_id"] = str(flag.id) if flag else None
        return Response(result)

    @action(detail=False, methods=["POST"])
    def resolve(self, request):
        """Shortcut: resolve a game by id string."""
        game_id = request.data.get("game_id")
        flag = GameFlag.objects.filter(game_id=game_id).first()
        if not flag:
            return Response({"detail": "No flag for this game"}, status=status.HTTP_404_NOT_FOUND)
        serializer = GameFlagSerializer(
            flag, data=request.data, context={"request": request}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class SanctionViewSet(viewsets.ModelViewSet):
    """Sanctions (warning / limited / banned) applied to rule-breakers."""

    queryset = UserSanction.objects.all()
    serializer_class = UserSanctionSerializer
    filterset_fields = ["user_id", "action", "active"]

    def perform_create(self, serializer):
        serializer.save(applied_by=self.request.user.id)


class UserRadarView(APIView):
    """Per-user fair play overview."""

    def get(self, request, user_id):
        open_flags = GameFlag.objects.filter(user_id=user_id, status=GameFlag.Status.OPEN).count()
        signals = CheatSignal.objects.filter(user_id=user_id).count()
        sanctions = list(
            UserSanction.objects.filter(user_id=user_id, active=True).values(
                "action", "reason", "created_at"
            )[:10]
        )
        return Response(
            {
                "user_id": user_id,
                "open_flags": open_flags,
                "total_signals": signals,
                "active_sanctions": sanctions,
                "needs_sanction": open_flags >= settings.ANTICHEAT_SANCTION_AFTER_FLAGS,
            }
        )


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        from django.db import connection

        db_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            db_ok = False
        return Response(
            {
                "status": "ok" if db_ok else "degraded",
                "service": "anticheat-service",
                "version": "1.0.0",
                "database": "ok" if db_ok else "error",
            },
            status=status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        )