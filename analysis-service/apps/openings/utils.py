"""
Opening detection utilities.
Matches a PGN or sequence of moves against the ECO openings database.
"""

import chess
import chess.pgn
from typing import Tuple, Optional
from .models import Opening


def detect_opening(pgn: str) -> Tuple[str, str]:
    """
    Detect the ECO opening code and name from a PGN string.

    Returns (eco_code, opening_name) — e.g. ("C00", "French Defense")
    Falls back to ("", "Unknown Opening").
    """
    try:
        game = chess.pgn.read_game(pgn.split("\n"))
        if game is None:
            return ("", "Unknown Opening")

        board = game.board()
        move_uci = []

        for move_node in game.mainline():
            board.push(move_node.move)
            move_uci.append(move_node.move.uci())

        return _match_opening(move_uci)
    except Exception:
        return ("", "Unknown Opening")


def detect_opening_from_moves(moves_uci: list) -> Tuple[str, str]:
    """Detect opening from a list of UCI moves."""
    return _match_opening(moves_uci)


def detect_opening_from_fen(fen: str) -> Tuple[str, str]:
    """Detect opening from a FEN position."""
    try:
        board = chess.Board(fen)
        # Reconstruct moves by going back to start
        game = chess.pgn.Game()
        node = game
        for move in board.move_stack:
            node = node.add_variation(move)

        move_uci = [m.uci() for m in board.move_stack]
        return _match_opening(move_uci)
    except Exception:
        return ("", "Unknown Opening")


def _match_opening(moves_uci: list) -> Tuple[str, str]:
    """Find best matching opening for a sequence of moves."""
    if not moves_uci:
        return ("", "Starting Position")

    moves_str = " ".join(moves_uci)

    # Find the opening with the longest matching prefix
    best_match = None
    best_len = 0

    openings = Opening.objects.all()
    for opening in openings:
        open_moves = opening.moves.strip()
        if moves_str.startswith(open_moves) and len(open_moves.split()) > best_len:
            best_match = opening
            best_len = len(open_moves.split())

    if best_match:
        return (best_match.eco, best_match.name)

    return ("", "Unknown Opening")
