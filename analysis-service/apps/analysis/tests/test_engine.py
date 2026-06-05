"""
Tests for the Stockfish engine wrapper.
Note: These tests require Stockfish to be installed.
Skip with: pytest -m "not stockfish"
"""

import pytest
from apps.analysis.engine import StockfishEngine, AnalysisDepth


@pytest.mark.stockfish
class TestStockfishEngine:
    def test_engine_available(self):
        engine = StockfishEngine()
        assert engine.is_available() is True
        engine.close()

    def test_analyze_starting_position(self):
        engine = StockfishEngine()
        result = engine.analyze_position(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            depth=10,
        )
        assert result["depth"] == 10
        assert isinstance(result["score"], int)
        assert len(result["bestMove"]) >= 4
        engine.close()

    def test_analyze_mate_position(self):
        """Position where white has a mate in 1: Qh7#"""
        engine = StockfishEngine()
        result = engine.analyze_position(
            "1k6/8/8/8/8/8/5Q2/6K1 w - - 0 1",
            depth=10,
        )
        assert result["mate"] is not None
        assert abs(result["mate"]) <= 1
        engine.close()

    def test_best_move(self):
        engine = StockfishEngine()
        result = engine.get_best_move(
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
            depth=10,
        )
        assert result["bestMove"] is not None
        assert len(result["topMoves"]) > 0
        engine.close()

    def test_game_analysis(self):
        pgn = """[Event "Test"]
1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6
5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O
9. h3 Nb8 10. d4 Nbd7
"""
        engine = StockfishEngine()
        result = engine.analyze_game(pgn, depth=8)
        assert result["totalMoves"] > 0
        assert result["analyzedMoves"] > 0
        assert "accuracy" in result
        assert "averageCentipawnLoss" in result
        engine.close()
