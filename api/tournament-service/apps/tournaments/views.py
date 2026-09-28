from django.db import models as db_models
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Tournament, TournamentPlayer, TournamentRound, TournamentMatch
from .serializers import (
    TournamentSerializer,
    TournamentCreateSerializer,
    TournamentPlayerSerializer,
    TournamentRoundSerializer,
    TournamentMatchSerializer,
    TournamentStandingSerializer,
)
from .swiss import pair_swiss_round, calculate_tiebreaks
from .round_robin import pair_round_robin_round


class TournamentViewSet(viewsets.ModelViewSet):
    queryset = Tournament.objects.all()
    serializer_class = TournamentSerializer
    filterset_fields = ["status", "type"]

    def get_serializer_class(self):
        if self.action == "create":
            return TournamentCreateSerializer
        return TournamentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = request.user.id
        instance = serializer.save(creator_id=user_id)
        output_serializer = TournamentSerializer(instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["GET"])
    def my(self, request):
        user_id = request.user.id
        tournaments = Tournament.objects.filter(
            id__in=TournamentPlayer.objects.filter(user_id=user_id).values("tournament_id")
        )
        page = self.paginate_queryset(tournaments)
        serializer = self.get_serializer(page if page else tournaments, many=True)
        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)

    @action(detail=True, methods=["POST"])
    def join(self, request, pk=None):
        tournament = self.get_object()
        user_id = request.user.id

        if tournament.status not in [Tournament.Status.PENDING, Tournament.Status.ACTIVE]:
            return Response({"detail": "Tournament is not accepting players"}, status=status.HTTP_400_BAD_REQUEST)

        if TournamentPlayer.objects.filter(tournament=tournament, user_id=user_id).exists():
            return Response({"detail": "Already joined"}, status=status.HTTP_400_BAD_REQUEST)

        if tournament.players.count() >= tournament.max_players:
            return Response({"detail": "Tournament is full"}, status=status.HTTP_400_BAD_REQUEST)

        player = TournamentPlayer.objects.create(
            tournament=tournament,
            user_id=user_id,
            seed=tournament.players.count() + 1,
        )
        serializer = TournamentPlayerSerializer(player)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["POST"])
    def leave(self, request, pk=None):
        tournament = self.get_object()
        user_id = request.user.id

        if tournament.status not in [Tournament.Status.PENDING]:
            return Response({"detail": "Can only leave pending tournaments"}, status=status.HTTP_400_BAD_REQUEST)

        deleted, _ = TournamentPlayer.objects.filter(tournament=tournament, user_id=user_id).delete()
        if deleted == 0:
            return Response({"detail": "Not a participant"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"detail": "Left tournament"})

    @action(detail=True, methods=["POST"])
    def start(self, request, pk=None):
        tournament = self.get_object()
        user_id = request.user.id

        if tournament.creator_id != user_id:
            return Response({"detail": "Only the creator can start the tournament"}, status=status.HTTP_403_FORBIDDEN)

        if tournament.status != Tournament.Status.PENDING:
            return Response({"detail": "Tournament already started or finished"}, status=status.HTTP_400_BAD_REQUEST)

        player_count = tournament.players.filter(is_active=True).count()
        if player_count < tournament.min_players:
            return Response({"detail": f"Need at least {tournament.min_players} players"}, status=status.HTTP_400_BAD_REQUEST)

        tournament.status = Tournament.Status.ACTIVE
        tournament.start_date = timezone.now()
        tournament.save(update_fields=["status", "start_date"])

        if tournament.type == Tournament.Type.ROUND_ROBIN:
            n = player_count
            tournament.total_rounds = n - 1 if n % 2 == 0 else n
            tournament.save(update_fields=["total_rounds"])

        pair_next_round(tournament)
        return Response(self.get_serializer(tournament).data)

    @action(detail=True, methods=["GET"])
    def standings(self, request, pk=None):
        tournament = self.get_object()

        players = TournamentPlayer.objects.filter(
            tournament=tournament, is_active=True
        ).order_by("-score", "-tiebreak1", "-tiebreak2")

        matches = TournamentMatch.objects.filter(
            tournament=tournament,
            round__status=TournamentRound.Status.COMPLETED,
        ).exclude(result=TournamentMatch.Result.NOT_PLAYED)

        match_stats = {}
        for m in matches:
            for uid in [m.white_player.user_id if m.white_player else None,
                        m.black_player.user_id if m.black_player else None]:
                if uid:
                    match_stats.setdefault(uid, {"wins": 0, "losses": 0, "draws": 0, "byes": 0})
            if m.result == TournamentMatch.Result.BYE:
                if m.white_player:
                    match_stats.setdefault(m.white_player.user_id, {"wins": 0, "losses": 0, "draws": 0, "byes": 0})
                    match_stats[m.white_player.user_id]["byes"] += 1
                continue
            if m.white_player and m.black_player:
                w_uid = m.white_player.user_id
                b_uid = m.black_player.user_id
                match_stats.setdefault(w_uid, {"wins": 0, "losses": 0, "draws": 0, "byes": 0})
                match_stats.setdefault(b_uid, {"wins": 0, "losses": 0, "draws": 0, "byes": 0})
                if m.result == TournamentMatch.Result.WHITE_WIN:
                    match_stats[w_uid]["wins"] += 1
                    match_stats[b_uid]["losses"] += 1
                elif m.result == TournamentMatch.Result.BLACK_WIN:
                    match_stats[b_uid]["wins"] += 1
                    match_stats[w_uid]["losses"] += 1
                elif m.result == TournamentMatch.Result.DRAW:
                    match_stats[w_uid]["draws"] += 1
                    match_stats[b_uid]["draws"] += 1

        standings = []
        for i, p in enumerate(players):
            stats = match_stats.get(p.user_id, {"wins": 0, "losses": 0, "draws": 0, "byes": 0})
            standings.append({
                "rank": i + 1,
                "user_id": p.user_id,
                "username": "",
                "score": p.score,
                "tiebreak1": p.tiebreak1,
                "tiebreak2": p.tiebreak2,
                **stats,
            })

        page = self.paginate_queryset(standings)
        serializer = TournamentStandingSerializer(page if page else standings, many=True)
        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)

    @action(detail=True, methods=["GET"])
    def matches(self, request, pk=None):
        tournament = self.get_object()
        round_id = request.query_params.get("round_id")
        round_number = request.query_params.get("round_number")

        qs = TournamentMatch.objects.filter(tournament=tournament).select_related("round", "white_player", "black_player")
        if round_id:
            qs = qs.filter(round_id=round_id)
        elif round_number:
            qs = qs.filter(round__round_number=round_number)

        page = self.paginate_queryset(qs)
        serializer = TournamentMatchSerializer(page if page else qs, many=True)
        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)

    @action(detail=True, methods=["GET"])
    def rounds(self, request, pk=None):
        tournament = self.get_object()
        rounds = TournamentRound.objects.filter(tournament=tournament).order_by("round_number")
        serializer = TournamentRoundSerializer(rounds, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["POST"])
    def pair(self, request, pk=None):
        tournament = self.get_object()
        user_id = request.user.id

        if tournament.creator_id != user_id:
            return Response({"detail": "Only the creator can pair rounds"}, status=status.HTTP_403_FORBIDDEN)

        if tournament.status != Tournament.Status.ACTIVE:
            return Response({"detail": "Tournament is not active"}, status=status.HTTP_400_BAD_REQUEST)

        if tournament.current_round >= tournament.total_rounds:
            return Response({"detail": "All rounds completed"}, status=status.HTTP_400_BAD_REQUEST)

        current_round_matches = TournamentMatch.objects.filter(
            tournament=tournament,
            round__status=TournamentRound.Status.ACTIVE,
        )
        if current_round_matches.filter(status=TournamentMatch.Status.PENDING).exists():
            return Response({"detail": "Current round has unfinished matches"}, status=status.HTTP_400_BAD_REQUEST)

        calculate_tiebreaks(tournament.id)
        round_obj = pair_next_round(tournament)
        if round_obj is None:
            return Response({"detail": "Could not create next round"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TournamentRoundSerializer(round_obj)
        return Response(serializer.data)

    @action(detail=True, methods=["POST"])
    def report(self, request, pk=None):
        tournament = self.get_object()
        match_id = request.data.get("match_id")
        result = request.data.get("result")

        if not match_id or not result:
            return Response({"detail": "match_id and result are required"}, status=status.HTTP_400_BAD_REQUEST)

        if result not in [TournamentMatch.Result.WHITE_WIN, TournamentMatch.Result.BLACK_WIN,
                          TournamentMatch.Result.DRAW]:
            return Response({"detail": "Invalid result"}, status=status.HTTP_400_BAD_REQUEST)

        match = get_object_or_404(TournamentMatch, id=match_id, tournament=tournament)
        if match.status == TournamentMatch.Status.COMPLETED:
            return Response({"detail": "Match already completed"}, status=status.HTTP_400_BAD_REQUEST)

        match.result = result
        match.status = TournamentMatch.Status.COMPLETED
        match.save(update_fields=["result", "status"])

        if match.white_player:
            if result == TournamentMatch.Result.WHITE_WIN:
                match.white_player.score += 1.0
            elif result == TournamentMatch.Result.DRAW:
                match.white_player.score += 0.5
                match.black_player.score += 0.5 if match.black_player else 0
            elif result == TournamentMatch.Result.BLACK_WIN:
                match.black_player.score += 1.0
            match.white_player.save(update_fields=["score"])
            if match.black_player:
                match.black_player.save(update_fields=["score"])

        calculate_tiebreaks(tournament.id)

        all_completed = not TournamentMatch.objects.filter(
            tournament=tournament,
            round=match.round,
            status=TournamentMatch.Status.PENDING,
        ).exists()

        if all_completed:
            match.round.status = TournamentRound.Status.COMPLETED
            match.round.completed_at = timezone.now()
            match.round.save(update_fields=["status", "completed_at"])

            is_last_round = tournament.current_round >= tournament.total_rounds
            if is_last_round:
                tournament.status = Tournament.Status.COMPLETED
                tournament.end_date = timezone.now()
                tournament.save(update_fields=["status", "end_date"])

        return Response(TournamentMatchSerializer(match).data)


def pair_next_round(tournament):
    if tournament.type == Tournament.Type.SWISS:
        return pair_swiss_round(tournament.id)
    elif tournament.type == Tournament.Type.ROUND_ROBIN:
        return pair_round_robin_round(tournament.id)
    return None
