"""Game-state helpers shared by the views."""
import chess

from .models import AIGame


def apply_move(game: AIGame, move: dict) -> None:
    """Trusted to be legal; applies an AI move to the stored game."""
    board = chess.Board(game.fen)
    uci = move["from"] + move["to"] + (move.get("promotion") or "")
    try:
        mv = board.parse_uci(uci)
    except ValueError:
        return
    if mv not in board.legal_moves:
        return
    san = board.san(mv)
    board.push(mv)
    game.fen = board.fen()
    game.moves = game.moves + [san]
    game.result = result_for_board(board)
    if board.is_game_over():
        game.draw_reason = board.outcome().termination.name if board.outcome() else ""
    game.save()


def result_for_board(board: chess.Board) -> str:
    """Map a chess.Board outcome to AI game result."""
    if not board.is_game_over():
        return AIGame.Result.PENDING
    if board.is_checkmate():
        # Side to move is mated
        return AIGame.Result.AI_WIN if board.turn == chess.WHITE else AIGame.Result.PLAYER_WIN
    return AIGame.Result.DRAW