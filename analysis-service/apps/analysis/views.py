from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GameAnalysis, AnalysisStatus, CachedPosition
from .serializers import (
    GameAnalysisSerializer,
    RequestAnalysisSerializer,
    PositionAnalysisSerializer,
)
from .tasks import analyze_game_task
from .engine import StockfishEngine


class RequestGameAnalysisView(APIView):
    """Submit a game for analysis."""

    def post(self, request):
        serializer = RequestAnalysisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        userId = getattr(request.user, "id", "system")

        analysis, created = GameAnalysis.objects.get_or_create(
            gameId=data["gameId"],
            defaults={
                "pgn": data["pgn"],
                "fen": data["fen"],
                "depth": data["depth"],
                "requestedBy": userId,
            },
        )

        if not created:
            if analysis.status == AnalysisStatus.COMPLETED:
                return Response(GameAnalysisSerializer(analysis).data)
            elif analysis.status == AnalysisStatus.ANALYZING:
                return Response(
                    {"success": True, "message": "Already analyzing", "data": GameAnalysisSerializer(analysis).data},
                )

        # Queue analysis
        analyze_game_task.delay(analysis.id)

        return Response(
            GameAnalysisSerializer(analysis).data,
            status=status.HTTP_202_ACCEPTED,
        )


class GetGameAnalysisView(APIView):
    """Get analysis results for a game."""

    def get(self, request, gameId):
        try:
            analysis = GameAnalysis.objects.get(gameId=gameId)
        except GameAnalysis.DoesNotExist:
            return Response(
                {"success": False, "message": "Analysis not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(GameAnalysisSerializer(analysis).data)


class GetGameAnalysisStatusView(APIView):
    """Get analysis progress status."""

    def get(self, request, gameId):
        try:
            analysis = GameAnalysis.objects.get(gameId=gameId)
        except GameAnalysis.DoesNotExist:
            return Response(
                {"success": False, "message": "Analysis not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({
            "gameId": analysis.gameId,
            "status": analysis.status,
            "totalMoves": analysis.totalMoves,
            "analyzedMoves": analysis.analyzedMoves,
            "progress": round(analysis.analyzedMoves / max(analysis.totalMoves, 1) * 100, 1),
            "createdAt": analysis.createdAt,
            "completedAt": analysis.completedAt,
        })


class AnalyzePositionView(APIView):
    """Analyze a single position (FEN)."""

    def post(self, request):
        serializer = PositionAnalysisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fen = serializer.validated_data["fen"]
        depth = serializer.validated_data["depth"]
        multipv = serializer.validated_data["multipv"]

        # Check cache first
        cached = CachedPosition.objects.filter(fen=fen, depth__gte=depth).order_by("-depth").first()
        if cached:
            return Response({
                "cached": True,
                "fen": cached.fen,
                "depth": cached.depth,
                "score": cached.score,
                "mate": cached.mate,
                "bestMove": cached.bestMove,
                "continuation": cached.continuation,
            })

        try:
            engine = StockfishEngine()
            result = engine.analyze_position(fen, depth, multipv)

            # Cache position
            CachedPosition.objects.update_or_create(
                fen=fen,
                defaults={
                    "depth": result["depth"],
                    "score": result["score"],
                    "mate": result["mate"],
                    "bestMove": result.get("bestMove", ""),
                    "continuation": result.get("continuation", []),
                    "nodesSearched": result.get("nodesSearched", 0),
                    "timeMs": result.get("timeMs", 0),
                },
            )

            return Response(result)
        except Exception as e:
            return Response(
                {"success": False, "message": f"Analysis failed: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class GetBestMoveView(APIView):
    """Get best move for a position."""

    def post(self, request):
        fen = request.data.get("fen")
        depth = request.data.get("depth", 18)

        if not fen:
            return Response(
                {"success": False, "message": "FEN is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            engine = StockfishEngine()
            result = engine.get_best_move(fen, depth)
            return Response(result)
        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
