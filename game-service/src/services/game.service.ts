import { v4 as uuidv4 } from "uuid";
import { GameModel, IGame, IPlayerInfo, ITimeControl, Termination } from "../models";
import { ChessEngine } from "./chess-engine";
import { redis, RedisKeys } from "../config/redis";
import { logger } from "../utils/logger";

const DEFAULT_TIME_CONTROLS: Record<string, ITimeControl> = {
  bullet: { initial: 60, increment: 0 },
  blitz: { initial: 300, increment: 3 },
  rapid: { initial: 600, increment: 5 },
  classical: { initial: 3600, increment: 10 },
};

export const GameService = {
  async createGame(
    player: IPlayerInfo,
    timeControlKey: string = "rapid",
    startingFen?: string
  ): Promise<IGame> {
    const tc = DEFAULT_TIME_CONTROLS[timeControlKey] || DEFAULT_TIME_CONTROLS.rapid;
    const initialFen = startingFen || "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

    const game = new GameModel({
      gameId: uuidv4(),
      players: {
        white: player,
        black: null,
      },
      status: "WAITING",
      timeControl: tc,
      clocks: { white: tc.initial, black: tc.initial },
      fen: initialFen,
      startingFen: initialFen,
      pgn: "",
      moves: [],
    });

    await game.save();

    await redis.setex(
      RedisKeys.userGame(player.userId),
      86400,
      game.gameId
    );

    logger.info(`Game created: ${game.gameId} by ${player.username}`);
    return game;
  },

  async joinGame(gameId: string, player: IPlayerInfo): Promise<IGame> {
    const game = await GameModel.findOne({ gameId });

    if (!game) {
      throw new Error("GAME_NOT_FOUND");
    }

    if (game.status !== "WAITING") {
      throw new Error("GAME_NOT_AVAILABLE");
    }

    if (game.players.white.userId === player.userId) {
      throw new Error("ALREADY_IN_GAME");
    }

    // Randomly assign colors (first player is white, second is black)
    game.players.black = player;
    game.status = "ACTIVE";
    game.clocks = {
      white: game.timeControl.initial,
      black: game.timeControl.initial,
    };
    await game.save();

    logger.info(`Player ${player.username} joined game: ${gameId}`);
    return game;
  },

  async getGame(gameId: string): Promise<IGame | null> {
    return GameModel.findOne({ gameId });
  },

  async getUserGames(
    userId: string,
    status?: string,
    limit: number = 20,
    skip: number = 0
  ): Promise<{ games: IGame[]; total: number }> {
    const query: any = {
      $or: [
        { "players.white.userId": userId },
        { "players.black.userId": userId },
      ],
    };

    if (status) {
      query.status = status;
    }

    const [games, total] = await Promise.all([
      GameModel.find(query)
        .sort({ createdAt: -1 })
        .skip(skip)
        .limit(limit)
        .lean(),
      GameModel.countDocuments(query),
    ]);

    return { games, total };
  },

  async makeMove(
    gameId: string,
    userId: string,
    from: string,
    to: string,
    promotion?: string
  ): Promise<{
    game: IGame;
    moveResult: any;
  }> {
    const game = await GameModel.findOne({ gameId });

    if (!game) throw new Error("GAME_NOT_FOUND");
    if (game.status !== "ACTIVE") throw new Error("GAME_NOT_ACTIVE");

    const isWhite = game.players.white.userId === userId;
    const isBlack = game.players.black?.userId === userId;
    if (!isWhite && !isBlack) throw new Error("NOT_YOUR_GAME");

    const engine = new ChessEngine(game.fen);
    const expectedTurn = engine.getTurn();

    if ((expectedTurn === "w" && !isWhite) || (expectedTurn === "b" && !isBlack)) {
      throw new Error("NOT_YOUR_TURN");
    }

    const result = engine.makeMove(from, to, promotion);
    if (!result.valid || !result.move) {
      throw new Error(result.error || "INVALID_MOVE");
    }

    // Calculate clock
    const now = Date.now();
    const lastMoveTime = game.lastMoveAt?.getTime() || now;
    const elapsed = Math.floor((now - lastMoveTime) / 1000);

    const turnColor = result.move.color;
    const clockKey = turnColor === "w" ? "white" : "black";
    game.clocks[clockKey] = Math.max(
      0,
      game.clocks[clockKey] - elapsed + game.timeControl.increment
    );

    // Check timeout
    if (game.clocks[clockKey] <= 0) {
      game.clocks[clockKey] = 0;
      game.status = "COMPLETED";
      game.result = turnColor === "w" ? "BLACK_WIN" : "WHITE_WIN";
      game.termination = "TIMEOUT";
      game.winner = turnColor === "w" ? game.players.black?.userId : game.players.white.userId;
      game.completedAt = new Date();
    }

    // Add move
    game.moves.push({
      moveNumber: result.move.moveNumber,
      from: result.move.from,
      to: result.move.to,
      promotion: result.move.promotion,
      fen: result.move.fen,
      san: result.move.san,
      piece: result.move.piece,
      color: result.move.color,
      timestamp: new Date(now),
      clock: game.clocks[clockKey],
    });

    game.fen = result.move.fen;
    game.pgn = engine.state.pgn;
    game.lastMoveAt = new Date(now);
    game.drawOffer = null;

    // Check game over
    if (result.gameOver) {
      game.status = "COMPLETED";
      game.termination = result.termination || null;

      if (result.winner) {
        game.result = result.winner === "w" ? "WHITE_WIN" : "BLACK_WIN";
        game.winner = result.winner === "w" ? game.players.white.userId : game.players.black?.userId;
      } else {
        game.result = "DRAW";
      }

      game.completedAt = new Date();

      // Notify user service about game result
      await this.notifyUserService(game, result);
    }

    await game.save();
    return { game, moveResult: result };
  },

  async resign(gameId: string, userId: string): Promise<IGame> {
    const game = await GameModel.findOne({ gameId });
    if (!game) throw new Error("GAME_NOT_FOUND");
    if (game.status !== "ACTIVE") throw new Error("GAME_NOT_ACTIVE");

    const isWhite = game.players.white.userId === userId;
    const isBlack = game.players.black?.userId === userId;
    if (!isWhite && !isBlack) throw new Error("NOT_YOUR_GAME");

    game.status = "COMPLETED";
    game.result = isWhite ? "BLACK_WIN" : "WHITE_WIN";
    game.termination = "RESIGNATION";
    game.winner = isWhite ? game.players.black?.userId : game.players.white.userId;
    game.completedAt = new Date();

    await game.save();

    await this.notifyUserService(game, { winner: isWhite ? "b" : "w" });

    logger.info(`Player ${userId} resigned from game: ${gameId}`);
    return game;
  },

  async offerDraw(gameId: string, userId: string): Promise<IGame> {
    const game = await GameModel.findOne({ gameId });
    if (!game) throw new Error("GAME_NOT_FOUND");
    if (game.status !== "ACTIVE") throw new Error("GAME_NOT_ACTIVE");

    game.drawOffer = userId;
    await game.save();
    return game;
  },

  async acceptDraw(gameId: string, userId: string): Promise<IGame> {
    const game = await GameModel.findOne({ gameId });
    if (!game) throw new Error("GAME_NOT_FOUND");
    if (game.status !== "ACTIVE") throw new Error("GAME_NOT_ACTIVE");
    if (game.drawOffer !== userId && game.drawOffer !== game.players.white.userId && game.drawOffer !== game.players.black?.userId) {
      throw new Error("NO_DRAW_OFFER");
    }

    game.status = "COMPLETED";
    game.result = "DRAW";
    game.termination = "DRAW_AGREEMENT";
    game.drawOffer = null;
    game.completedAt = new Date();

    await game.save();

    await this.notifyUserService(game, { winner: null });

    logger.info(`Draw accepted in game: ${gameId}`);
    return game;
  },

  async declineDraw(gameId: string, userId: string): Promise<IGame> {
    const game = await GameModel.findOne({ gameId });
    if (!game) throw new Error("GAME_NOT_FOUND");

    game.drawOffer = null;
    await game.save();
    return game;
  },

  async abandonGame(gameId: string, userId: string): Promise<IGame> {
    const game = await GameModel.findOne({ gameId });
    if (!game) throw new Error("GAME_NOT_FOUND");

    if (game.status === "WAITING") {
      if (game.players.white.userId === userId) {
        game.status = "ABANDONED";
        await game.save();
        return game;
      }
      throw new Error("NOT_YOUR_GAME");
    }

    // For active games, treat as resign
    return this.resign(gameId, userId);
  },

  async getClock(gameId: string): Promise<{ white: number; black: number } | null> {
    const cached = await redis.get(RedisKeys.clockTick(gameId));
    if (cached) {
      return JSON.parse(cached);
    }

    const game = await GameModel.findOne({ gameId });
    if (!game || game.status !== "ACTIVE") return null;

    return { white: game.clocks.white, black: game.clocks.black };
  },

  async notifyUserService(game: IGame, result: any): Promise<void> {
    try {
      const { default: axios } = await import("axios");
      const { env } = await import("../config/env");

      const tcKey = this._getTimeControlKey(game.timeControl);

      // 1. Notify user service (basic stats)
      const players = [game.players.white, game.players.black].filter(Boolean);
      for (const player of players) {
        if (!player) continue;

        const isWhite = game.players.white.userId === player.userId;
        let gameResult: "win" | "loss" | "draw" = "draw";
        if (result.winner === "w") gameResult = isWhite ? "win" : "loss";
        else if (result.winner === "b") gameResult = isWhite ? "loss" : "win";

        const opponentRating = isWhite
          ? game.players.black?.rating || 1200
          : game.players.white.rating;

        await axios.post(
          `${env.USER_SERVICE_URL}/api/users/stats/record`,
          { result: gameResult, timeControl: tcKey, opponentRating },
          {
            headers: {
              "X-User-Id": player.userId,
              "X-User-Email": "game-service@internal",
              "X-User-Role": "SYSTEM",
            },
            timeout: 5000,
          }
        ).catch(() => {}); // Fire-and-forget
      }

      // 2. Notify rating service (Glicko-2 calculation)
      const gameResultStr = result.winner === "w" ? "1-0" : result.winner === "b" ? "0-1" : "1/2-1/2";
      await axios.post(
        `${env.RATING_SERVICE_URL}/api/ratings/update`,
        {
          gameId: game.gameId,
          whiteUserId: game.players.white.userId,
          blackUserId: game.players.black?.userId,
          result: gameResultStr,
          timeControl: tcKey,
          playedAt: game.completedAt?.toISOString() || new Date().toISOString(),
        },
        {
          headers: { "Content-Type": "application/json" },
          timeout: 5000,
        }
      ).catch(() => {});
    } catch (err) {
      logger.error(`Failed to notify services for game ${game.gameId}:`, err);
    }
  },

  _getTimeControlKey(tc: { initial: number; increment: number }): string {
    if (tc.initial <= 60) return "bullet";
    if (tc.initial <= 300) return "blitz";
    if (tc.initial <= 1800) return "rapid";
    return "classical";
  },
};

export { DEFAULT_TIME_CONTROLS };
