"""
Stockfish chess engine wrapper for game and position analysis.

Uses the Stockfish UCI protocol via python-stockfish library.
Handles engine lifecycle, analysis queues, and result formatting.
"""

import logging
import chess
import chess.pgn
from typing import List, Dict, Optional, Tuple
from stockfish import Stockfish as StockfishLib
from django.conf import settings

logger = logging.getLogger(__name__)


class AnalysisDepth:
    QUICK = settings.ANALYSIS_QUICK_DEPTH  # 12
    NORMAL = settings.ANALYSIS_NORMAL_DEPTH  # 18
    DEEP = settings.ANALYSIS_DEEP_DEPTH  # 24


class StockfishEngine:
    """Thread-safe Stockfish wrapper. Create a new instance per analysis task."""

    def __init__(self):
        self._engine: Optional[StockfishLib] = None

    def _get_engine(self) -> StockfishLib:
        if self._engine is None:
            self._engine = StockfishLib(
                path=settings.STOCKFISH_PATH,
                parameters={
                    "Hash": settings.STOCKFISH_HASH_SIZE,
                    "Threads": settings.STOCKFISH_THREADS,
                    "Minimum Thinking Time": 20,
                },
            )
        return self._engine

    def is_available(self) -> bool:
        try:
            engine = self._get_engine()
            return engine.is_ready()
        except Exception as e:
            logger.error("Stockfish not available: %s", e)
            return False

    def analyze_position(
        self,
        fen: str,
        depth: int = AnalysisDepth.NORMAL,
        multipv: int = 1,
    ) -> Dict:
        """
        Analyze a single position at the given depth.

        Returns:
        {
            "fen": str,
            "depth": int,
            "score": int,       # centipawns (positive = white advantage)
            "mate": int | None, # moves to mate, if applicable
            "bestMove": str,     # UCI format, e.g. "e2e4"
            "continuation": [str],  # best line as UCI moves
            "nodesSearched": int,
            "timeMs": int,
        }
        """
        engine = self._get_engine()
        engine.set_fen_position(fen)
        engine.set_depth(depth)

        result = engine.get_evaluation()

        score = result.get("value", 0)
        is_mate = result.get("type") == "mate"
        mate = score if is_mate else None

        best_move = engine.get_best_move()
        board = chess.Board(fen)
        top_line = []

        # Get principal variation
        try:
            pv_info = engine.get_top_moves(multipv)
            if pv_info and len(pv_info) > 0:
                top_move = pv_info[0].get("Move", best_move)
                if not best_move:
                    best_move = top_move
                # Build continuation from PV
                if top_move:
                    test_board = chess.Board(fen)
                    test_board.push_uci(top_move)
                    top_line.append(top_move)
                    # Try to get a few more moves
                    engine2 = StockfishLib(
                        path=settings.STOCKFISH_PATH,
                        parameters={"Hash": 64, "Threads": 1},
                    )
                    engine2.set_fen_position(test_board.fen())
                    engine2.set_depth(max(4, depth - 6))
                    for _ in range(3):
                        next_move = engine2.get_best_move()
                        if next_move:
                            try:
                                test_board.push_uci(next_move)
                                top_line.append(next_move)
                            except ValueError:
                                break
                        else:
                            break
                    engine2.quit()
        except Exception:
            pass

        info = engine.get_info()
        nodes = info.get("nodes", 0)
        time = info.get("time", 0)

        return {
            "fen": fen,
            "depth": depth,
            "score": score if not is_mate else 0,
            "mate": mate,
            "bestMove": best_move or "",
            "continuation": top_line,
            "nodesSearched": nodes,
            "timeMs": time,
        }

    def analyze_game(
        self,
        pgn: str,
        depth: int = AnalysisDepth.NORMAL,
    ) -> Dict:
        """
        Analyze every move in a PGN game.

        Returns:
        {
            "totalMoves": int,
            "analyzedMoves": int,
            "moves": [{ "moveNumber", "san", "fen", "score", "mate",
                        "bestMove", "continuation", "blunder", "evalDiff" }],
            "accuracy": { "white": float, "black": float },
            "averageCentipawnLoss": { "white": float, "black": float },
        }
        """
        game = chess.pgn.read_game(pgn.split("\n"))
        if game is None:
            raise ValueError("Invalid PGN")

        board = game.board()
        analyzed_moves = []
        total_moves = 0
        prev_score = None
        prev_turn = None

        white_cp_losses = []
        black_cp_losses = []
        classification_counts = {"white": {"brilliant": 0, "good": 0, "inaccuracy": 0, "mistake": 0, "blunder": 0},
                                  "black": {"brilliant": 0, "good": 0, "inaccuracy": 0, "mistake": 0, "blunder": 0}}

        for move_node in game.mainline():
            total_moves += 1
            move = move_node.move
            san = board.san(move)
            fen_before = board.fen()

            # Analyze position before the move
            analysis = self.analyze_position(fen_before, depth)

            score_before = analysis["score"]
            best_move = analysis["bestMove"]

            # Make the move on the board
            board.push(move)
            fen_after = board.fen()

            # Calculate evaluation difference
            eval_diff = 0
            classification = None

            if prev_score is not None and prev_turn == board.turn:
                # How much did the player's position change from optimal?
                # If prev_score was the evaluation before THEIR move:
                # The optimal move would maintain prev_score
                # The actual move resulted in current_score
                current_analysis = self.analyze_position(fen_after, max(8, depth - 4))
                score_after = current_analysis["score"]

                if board.turn == chess.WHITE:
                    # From white's perspective, a drop in score (or more negative) = mistake
                    eval_diff = score_after - score_before
                else:
                    eval_diff = -(score_after - score_before)

                # Classify the move quality
                if prev_turn == chess.WHITE:
                    optimal_diff = score_before - prev_score if prev_score is not None else 0
                else:
                    optimal_diff = -(score_before - prev_score) if prev_score is not None else 0

                if eval_diff is not None:
                    abs_diff = abs(eval_diff)
                    if abs_diff >= 300:
                        classification = "blunder"
                    elif abs_diff >= 150:
                        classification = "mistake"
                    elif abs_diff >= 75:
                        classification = "inaccuracy"
                    elif abs_diff >= 30:
                        classification = "good"
                    else:
                        classification = "brilliant"

                    turn_key = "white" if board.turn == chess.BLACK else "black"
                    classification_counts[turn_key][classification] += 1

                    if eval_diff > 0:
                        if board.turn == chess.BLACK:
                            white_cp_losses.append(eval_diff)
                        else:
                            black_cp_losses.append(eval_diff)

            analyzed_move = {
                "moveNumber": total_moves,
                "san": san,
                "fen": fen_before,
                "score": score_before,
                "mate": analysis.get("mate"),
                "bestMove": best_move,
                "playedMove": move.uci(),
                "continuation": analysis.get("continuation", []),
                "evalDiff": round(eval_diff, 1) if eval_diff is not None else None,
                "classification": classification,
            }
            analyzed_moves.append(analyzed_move)

            prev_score = score_before
            prev_turn = board.turn

        # Calculate accuracy & average centipawn loss
        def calc_avg_loss(losses):
            return round(sum(losses) / len(losses), 1) if losses else 0.0

        avg_wcl = calc_avg_loss(white_cp_losses)
        avg_bcl = calc_avg_loss(black_cp_losses)

        # Simple accuracy formula: 100 - (avg_cp_loss / 10)
        white_acc = max(0, min(100, round(100 - avg_wcl / 10, 1)))
        black_acc = max(0, min(100, round(100 - avg_bcl / 10, 1)))

        return {
            "totalMoves": total_moves,
            "analyzedMoves": len(analyzed_moves),
            "moves": analyzed_moves,
            "accuracy": {"white": white_acc, "black": black_acc},
            "averageCentipawnLoss": {"white": avg_wcl, "black": avg_bcl},
            "classifications": classification_counts,
        }

    def get_best_move(self, fen: str, depth: int = AnalysisDepth.NORMAL) -> Dict:
        """Get the best move and top lines for a position."""
        engine = self._get_engine()
        engine.set_fen_position(fen)
        engine.set_depth(depth)

        best_move = engine.get_best_move()
        top_moves = []
        try:
            for pv in engine.get_top_moves(3):
                top_moves.append({
                    "move": pv.get("Move", ""),
                    "centipawn": pv.get("Centipawn", None),
                    "mate": pv.get("Mate", None),
                })
        except Exception:
            pass

        return {
            "fen": fen,
            "depth": depth,
            "bestMove": best_move,
            "topMoves": top_moves,
        }

    def close(self):
        if self._engine:
            try:
                self._engine.quit()
            except Exception:
                pass
            self._engine = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
