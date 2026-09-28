"""
Minimal but competent chess AI.

  - Negamax search with alpha-beta pruning
  - Fixed depths per difficulty level
  - Material + piece-square table evaluation (white perspective)
  - Configurable human-like mistakes for lower levels
"""
import math
import random

import chess

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

# Piece-square tables (from the white perspective, index 0 = a8, 63 = h1 style
# is avoided by using 0-63 row-major from a1). Tables below are from
# chessprogramming.org "Simplified Evaluation Function".
PAWN_TABLE = [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0,
]
KNIGHT_TABLE = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]
BISHOP_TABLE = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]
ROOK_TABLE = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, 10, 10, 10, 10, 5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    0, 0, 0, 5, 5, 0, 0, 0,
]
QUEEN_TABLE = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 5, 5, 5, 5, 5, 0, -10,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20,
]
KING_TABLE = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20,
]

_TABLES = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE,
    chess.KING: KING_TABLE,
}

MATE_SCORE = 100000


def evaluate(board: chess.Board) -> float:
    """Static evaluation in centipawns from White's perspective."""
    if board.is_checkmate():
        return -MATE_SCORE if board.turn == chess.WHITE else MATE_SCORE
    if board.is_game_over():
        return 0.0

    score = 0.0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None:
            continue
        value = PIECE_VALUES[piece.piece_type]
        table = _TABLES[piece.piece_type]

        if piece.color == chess.WHITE:
            total = value + table[square]
        else:
            total = -value - table[chess.square_mirror(square)]
        score += total

    return score


def order_moves(board: chess.Board) -> list[chess.Move]:
    """Cheap move ordering: captures first, then promotion, then MVV-LVA."""

    def key(move):
        score = 0
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim and attacker:
                score += 10 * PIECE_VALUES[victim.piece_type] - PIECE_VALUES[attacker.piece_type]
            else:
                score += 500
        if move.promotion:
            score += 800
        return -score

    return sorted(board.legal_moves, key=key)


def _negamax(board, depth, alpha, beta) -> float:
    """Negamax with alpha-beta pruning. Positive scores favor the side to move."""
    if board.is_game_over():
        return -_terminal_score(board)

    if depth == 0:
        # Slight preference for the side to move keeps play dynamic.
        return _side_to_move_bias(board)

    best = -math.inf
    for move in order_moves(board):
        board.push(move)
        score = -_negamax(board, depth - 1, -beta, -alpha)
        board.pop()
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def _terminal_score(board) -> float:
    if board.is_checkmate():
        return MATE_SCORE
    return 0.0


def _side_to_move_bias(board) -> float:
    """Return evaluation from the mover's perspective (negamax needs it)."""
    from_white = evaluate(board)
    return from_white if board.turn == chess.WHITE else -from_white


def best_move(board: chess.Board, depth: int = 3) -> tuple[chess.Move | None, float]:
    """Return (best move from the side to move, score in centipawns)."""
    b = board.copy()
    moves = order_moves(b)
    if not moves:
        return None, 0.0

    best = None
    best_score = -math.inf
    alpha = -math.inf
    beta = math.inf
    for move in moves:
        b.push(move)
        score = -_negamax(b, depth - 1, -beta, -alpha)
        b.pop()
        if score > best_score:
            best_score = score
            best = move
        if best_score > alpha:
            alpha = best_score
    return best, best_score


def _pick_weak(board: chess.Board, depth: int, mistake_prob, blunder_prob) -> chess.Move:
    """Pick a move with occasional human errors for lower difficulties."""
    legal = list(board.legal_moves)
    if not legal:
        return None

    r = random.random()
    if r < blunder_prob:
        # Blunder: grab a materially bad or random move.
        return random.choice(legal)

    if r < blunder_prob + mistake_prob:
        # Mistake: pick second-best via a shallow search with jitter.
        moves_with_score = []
        shallow = board.copy()
        for move in legal:
            shallow.push(move)
            score = -_side_to_move_bias(shallow)
            moves_with_score.append((score + random.uniform(-60, 60), move))
            shallow.pop()
        moves_with_score.sort(key=lambda x: x[0], reverse=True)
        idx = random.choice([1, 2])
        return moves_with_score[min(idx, len(moves_with_score) - 1)][1]

    best, _ = best_move(board, depth=depth)
    return best or random.choice(legal)


def choose_move(fen: str, level: str = "medium") -> dict:
    """
    Public entry point: given a FEN, choose the AI's reply.

    Returns dict with from/to/promotion/san/score/depth or a null move if
    the game is already over.
    """
    from django.conf import settings

    config = settings.AI_LEVELS.get(level, settings.AI_LEVELS[settings.AI_DEFAULT_LEVEL])
    board = chess.Board(fen)

    if board.is_game_over():
        return {"move": None, "game_over": True, "result": board.result()}

    depth = config["depth"]
    mistake_prob = config.get("mistake_probability", 0.0)
    blunder_prob = config.get("blunder_probability", 0.0)

    if mistake_prob > 0 or blunder_prob > 0:
        move = _pick_weak(board, depth, mistake_prob, blunder_prob)
        _, score = best_move(board, depth=min(depth, 3))
    else:
        move, score = best_move(board, depth=depth)

    if move is None:
        return {"move": None, "game_over": True, "result": board.result()}

    return {
        "move": {
            "from": chess.square_name(move.from_square),
            "to": chess.square_name(move.to_square),
            "promotion": chess.piece_symbol(move.promotion) if move.promotion else None,
            "san": board.san(move),
        },
        "game_over": False,
        "score": round(score, 1),
        "level": level,
        "depth": depth,
    }