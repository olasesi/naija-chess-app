import mongoose, { Schema, Document } from "mongoose";

export interface IPlayerInfo {
  userId: string;
  username: string;
  rating: number;
}

export interface IMove {
  moveNumber: number;
  from: string;
  to: string;
  promotion?: string;
  fen: string;
  san: string;
  piece: string;
  color: "w" | "b";
  timestamp: Date;
  clock: number;
}

export type GameStatus = "WAITING" | "ACTIVE" | "COMPLETED" | "ABANDONED";
export type GameResult = "WHITE_WIN" | "BLACK_WIN" | "DRAW" | null;
export type Termination = "CHECKMATE" | "RESIGNATION" | "TIMEOUT" | "DRAW_AGREEMENT" | "STALEMATE" | "THREEFOLD_REPETITION" | "FIFTY_MOVES" | "INSUFFICIENT_MATERIAL" | "ABANDONMENT";

export interface ITimeControl {
  initial: number;
  increment: number;
}

export interface IGame extends Document {
  gameId: string;
  players: {
    white: IPlayerInfo;
    black: IPlayerInfo;
  };
  status: GameStatus;
  result: GameResult;
  termination: Termination;
  timeControl: ITimeControl;
  clocks: { white: number; black: number };
  lastMoveAt: Date | null;
  moves: IMove[];
  pgn: string;
  fen: string;
  startingFen: string;
  winner: string | null;
  drawOffer: string | null;
  createdAt: Date;
  updatedAt: Date;
  completedAt: Date | null;
}

const PlayerInfoSchema = new Schema<IPlayerInfo>(
  {
    userId: { type: String, required: true },
    username: { type: String, required: true },
    rating: { type: Number, required: true },
  },
  { _id: false }
);

const MoveSchema = new Schema<IMove>(
  {
    moveNumber: { type: Number, required: true },
    from: { type: String, required: true },
    to: { type: String, required: true },
    promotion: String,
    fen: { type: String, required: true },
    san: { type: String, required: true },
    piece: { type: String, required: true },
    color: { type: String, enum: ["w", "b"], required: true },
    timestamp: { type: Date, required: true },
    clock: { type: Number, required: true },
  },
  { _id: false }
);

const GameSchema = new Schema<IGame>(
  {
    gameId: { type: String, required: true, unique: true, index: true },
    players: {
      white: { type: PlayerInfoSchema, required: true },
      black: { type: PlayerInfoSchema, default: null },
    },
    status: {
      type: String,
      enum: ["WAITING", "ACTIVE", "COMPLETED", "ABANDONED"],
      default: "WAITING",
      index: true,
    },
    result: { type: String, enum: ["WHITE_WIN", "BLACK_WIN", "DRAW"], default: null },
    termination: {
      type: String,
      enum: [
        "CHECKMATE", "RESIGNATION", "TIMEOUT", "DRAW_AGREEMENT",
        "STALEMATE", "THREEFOLD_REPETITION", "FIFTY_MOVES",
        "INSUFFICIENT_MATERIAL", "ABANDONMENT",
      ],
      default: null,
    },
    timeControl: {
      initial: { type: Number, required: true, default: 600 },
      increment: { type: Number, required: true, default: 0 },
    },
    clocks: {
      white: { type: Number, required: true, default: 600 },
      black: { type: Number, required: true, default: 600 },
    },
    lastMoveAt: { type: Date, default: null },
    moves: [MoveSchema],
    pgn: { type: String, default: "" },
    fen: { type: String, required: true, default: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" },
    startingFen: { type: String, default: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" },
    winner: { type: String, default: null },
    drawOffer: { type: String, default: null },
    completedAt: { type: Date, default: null },
  },
  {
    timestamps: true,
    collection: "games",
  }
);

GameSchema.index({ "players.white.userId": 1 });
GameSchema.index({ "players.black.userId": 1 });
GameSchema.index({ status: 1, createdAt: -1 });

export const GameModel = mongoose.model<IGame>("Game", GameSchema);
