import pytest
from apps.openings.utils import detect_opening_from_moves, detect_opening_from_fen


class TestOpeningDetection:
    def test_italian_game(self):
        """1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5"""
        moves = ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5"]
        eco, name = detect_opening_from_moves(moves)
        assert name == "Italian Game"

    def test_sicilian_defense(self):
        """1.e4 c5"""
        moves = ["e2e4", "c7c5"]
        eco, name = detect_opening_from_moves(moves)
        assert eco == "B20"

    def test_ruy_lopez(self):
        """1.e4 e5 2.Nf3 Nc6 3.Bb5"""
        moves = ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"]
        eco, name = detect_opening_from_moves(moves)
        assert eco == "C60"
        assert "Lopez" in name

    def test_empty_moves(self):
        eco, name = detect_opening_from_moves([])
        assert name == "Starting Position"

    def test_french_defense(self):
        """1.e4 e6"""
        moves = ["e2e4", "e7e6"]
        eco, name = detect_opening_from_moves(moves)
        assert eco == "C00"

    def test_caro_kann(self):
        """1.e4 c6 2.d4 d5"""
        moves = ["e2e4", "c7c6", "d2d4", "d7d5"]
        eco, name = detect_opening_from_moves(moves)
        assert eco == "B12"
