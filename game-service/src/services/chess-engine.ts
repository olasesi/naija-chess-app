import { Chess } from "chess.js";
import { IMove, Termination } from "../models";

export interface MoveResult {
  valid: boolean;
  gameOver: boolean;
  terminated: boolean;
  termination?: Termination;
  winner?: "w" | "b" | null;
  move?: {
    from: string;
    to: string;
    promotion?: string;
    fen: string;
    san: string;
    piece: string;
    color: "w" | "b";
    moveNumber: number;
  };
  error?: string;
}

export interface GameState {
  fen: string;
  pgn: string;
  turn: "w" | "b";
  isGameOver: boolean;
  isCheck: boolean;
  isCheckmate: boolean;
  isDraw: boolean;
  isStalemate: boolean;
  isThreefoldRepetition: boolean;
  isInsufficientMaterial: boolean;
  isFiftyMoves: boolean;
  moveCount: number;
  lastMove?: { from: string; to: string; san: string };
}

export class ChessEngine {
  private chess: Chess;

  constructor(fen?: string) {
    this.chess = fen ? new Chess(fen) : new Chess();
  }

  get state(): GameState {
    const history = this.chess.history({ verbose: true });
    const last = history.length > 0 ? history[history.length - 1] : undefined;

    return {
      fen: this.chess.fen(),
      pgn: this.chess.pgn(),
      turn: this.chess.turn(),
      isGameOver: this.chess.isGameOver(),
      isCheck: this.chess.isCheck(),
      isCheckmate: this.chess.isCheckmate(),
      isDraw: this.chess.isDraw(),
      isStalemate: this.chess.isStalemate(),
      isThreefoldRepetition: this.chess.isThreefoldRepetition(),
      isInsufficientMaterial: this.chess.isInsufficientMaterial(),
      isFiftyMoves: this.chess.isFiftyMoves(),
      moveCount: this.chess.moveNumber(),
      lastMove: last ? { from: last.from, to: last.to, san: last.san } : undefined,
    };
  }

  makeMove(from: string, to: string, promotion?: string): MoveResult {
    try {
      const move = this.chess.move({ from, to, promotion });
      const state = this.state;

      let termination: Termination | undefined;
      let winner: "w" | "b" | null = null;

      if (state.isCheckmate) {
        termination = "CHECKMATE";
        winner = state.turn === "w" ? "b" : "w";
      } else if (state.isStalemate) {
        termination = "STALEMATE";
      } else if (state.isThreefoldRepetition) {
        termination = "THREEFOLD_REPETITION";
      } else if (state.isInsufficientMaterial) {
        termination = "INSUFFICIENT_MATERIAL";
      } else if (state.isFiftyMoves) {
        termination = "FIFTY_MOVES";
      }

      return {
        valid: true,
        gameOver: state.isGameOver,
        terminated: state.isGameOver,
        termination,
        winner,
        move: {
          from,
          to,
          promotion,
          fen: state.fen,
          san: move.san,
          piece: move.piece,
          color: move.color as "w" | "b",
          moveNumber: state.moveCount,
        },
      };
    } catch (err: any) {
      return {
        valid: false,
        gameOver: false,
        terminated: false,
        error: err.message || "Invalid move",
      };
    }
  }

  getTurn(): "w" | "b" {
    return this.chess.turn();
  }

  isGameOver(): boolean {
    return this.chess.isGameOver();
  }

  reset(): void {
    this.chess = new Chess();
  }

  load(fen: string): void {
    this.chess = new Chess(fen);
  }
}
