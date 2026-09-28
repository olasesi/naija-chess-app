import logging
from celery import shared_task
from django.utils import timezone

from .models import GameAnalysis, AnalysisStatus, CachedPosition
from .engine import StockfishEngine, AnalysisDepth

logger = logging.getLogger(__name__)

DEPTH_MAP = {
    "quick": AnalysisDepth.QUICK,
    "normal": AnalysisDepth.NORMAL,
    "deep": AnalysisDepth.DEEP,
}


@shared_task(bind=True, max_retries=1, soft_time_limit=600)
def analyze_game_task(self, analysis_id: int):
    """Run full game analysis via Stockfish."""
    try:
        analysis = GameAnalysis.objects.get(id=analysis_id)
    except GameAnalysis.DoesNotExist:
        logger.error(f"Analysis {analysis_id} not found")
        return

    analysis.status = AnalysisStatus.ANALYZING
    analysis.save(update_fields=["status"])

    depth = DEPTH_MAP.get(analysis.depth, AnalysisDepth.NORMAL)

    try:
        engine = StockfishEngine()
        if not engine.is_available():
            raise RuntimeError("Stockfish engine is not available")

        result = engine.analyze_game(analysis.pgn, depth)

        analysis.totalMoves = result["totalMoves"]
        analysis.analyzedMoves = result["analyzedMoves"]
        analysis.moves = result["moves"]
        analysis.accuracy = result["accuracy"]
        analysis.averageCentipawnLoss = result["averageCentipawnLoss"]
        analysis.classifications = result["classifications"]
        analysis.status = AnalysisStatus.COMPLETED
        analysis.completedAt = timezone.now()

        # Detect opening from PGN
        try:
            from apps.openings.utils import detect_opening
            eco, opening_name = detect_opening(analysis.pgn)
            analysis.eco = eco
            analysis.opening = opening_name
        except Exception:
            pass

        # Cache positions for future lookups
        _cache_analysis_positions(result["moves"], depth)

        analysis.save()
        logger.info(f"Analysis completed for game {analysis.gameId}")

    except Exception as e:
        logger.error(f"Analysis failed for {analysis.gameId}: {e}")
        analysis.status = AnalysisStatus.FAILED
        analysis.error = str(e)
        analysis.save(update_fields=["status", "error"])

        try:
            self.retry(countdown=60)
        except Exception:
            pass


def _cache_analysis_positions(moves: list, depth: int):
    """Cache analyzed positions to speed up future lookups."""
    for move_data in moves:
        fen = move_data.get("fen")
        if not fen:
            continue
        try:
            CachedPosition.objects.update_or_create(
                fen=fen,
                defaults={
                    "depth": depth,
                    "score": move_data.get("score", 0),
                    "mate": move_data.get("mate"),
                    "bestMove": move_data.get("bestMove", ""),
                    "continuation": move_data.get("continuation", []),
                    "nodesSearched": 0,
                    "timeMs": 0,
                },
            )
        except Exception:
            pass
