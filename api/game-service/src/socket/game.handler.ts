import { Server } from "socket.io";
import { AuthenticatedSocket } from "./auth.socket";
import { GameService } from "../services/game.service";
import { logger } from "../utils/logger";

const CLOCK_INTERVAL = 1000; // 1 second

export function registerGameHandlers(io: Server, socket: AuthenticatedSocket): void {
  const userId = socket.userId!;

  // ─── Join Game Room ──────────────────────────────────────────────────────
  socket.on("game:join", async (gameId: string, callback) => {
    try {
      const game = await GameService.getGame(gameId);
      if (!game) {
        return callback?.({ success: false, error: "Game not found" });
      }

      const isPlayer =
        game.players.white.userId === userId ||
        game.players.black?.userId === userId;

      if (!isPlayer) {
        return callback?.({ success: false, error: "Not a player in this game" });
      }

      socket.join(`game:${gameId}`);

      // Clear any previous clock interval for this socket
      clearClockInterval(socket);

      // If game is active, start clock
      if (game.status === "ACTIVE") {
        startClockForGame(io, gameId);
      }

      callback?.({ success: true, game });
    } catch (err: any) {
      callback?.({ success: false, error: err.message });
    }
  });

  // ─── Make Move ───────────────────────────────────────────────────────────
  socket.on("game:move", async (data: { gameId: string; from: string; to: string; promotion?: string }, callback) => {
    try {
      const { game, moveResult } = await GameService.makeMove(
        data.gameId,
        userId,
        data.from,
        data.to,
        data.promotion
      );

      // Broadcast move to all players in the game room
      io.to(`game:${data.gameId}`).emit("game:moveMade", {
        move: moveResult.move,
        fen: game.fen,
        pgn: game.pgn,
        clocks: game.clocks,
        turn: game.fen.split(" ")[1] === "w" ? "white" : "black",
      });

      // If game is over, broadcast result and stop clock
      if (game.status === "COMPLETED") {
        io.to(`game:${data.gameId}`).emit("game:over", {
          result: game.result,
          termination: game.termination,
          winner: game.winner,
          pgn: game.pgn,
          moves: game.moves,
        });
        stopClockForGame(data.gameId);
      }

      callback?.({ success: true, game });
    } catch (err: any) {
      callback?.({ success: false, error: err.message });
    }
  });

  // ─── Resign ──────────────────────────────────────────────────────────────
  socket.on("game:resign", async (gameId: string, callback) => {
    try {
      const game = await GameService.resign(gameId, userId);

      io.to(`game:${gameId}`).emit("game:over", {
        result: game.result,
        termination: game.termination,
        winner: game.winner,
        pgn: game.pgn,
        moves: game.moves,
      });

      stopClockForGame(gameId);
      callback?.({ success: true, game });
    } catch (err: any) {
      callback?.({ success: false, error: err.message });
    }
  });

  // ─── Draw Offer ──────────────────────────────────────────────────────────
  socket.on("game:drawOffer", async (gameId: string, callback) => {
    try {
      const game = await GameService.offerDraw(gameId, userId);
      io.to(`game:${gameId}`).emit("game:drawOffered", { by: userId });
      callback?.({ success: true });
    } catch (err: any) {
      callback?.({ success: false, error: err.message });
    }
  });

  // ─── Draw Accept ─────────────────────────────────────────────────────────
  socket.on("game:drawAccept", async (gameId: string, callback) => {
    try {
      const game = await GameService.acceptDraw(gameId, userId);

      io.to(`game:${gameId}`).emit("game:over", {
        result: "DRAW",
        termination: "DRAW_AGREEMENT",
        winner: null,
        pgn: game.pgn,
        moves: game.moves,
      });

      stopClockForGame(gameId);
      callback?.({ success: true });
    } catch (err: any) {
      callback?.({ success: false, error: err.message });
    }
  });

  // ─── Draw Decline ────────────────────────────────────────────────────────
  socket.on("game:drawDecline", async (gameId: string, callback) => {
    try {
      await GameService.declineDraw(gameId, userId);
      io.to(`game:${gameId}`).emit("game:drawDeclined", { by: userId });
      callback?.({ success: true });
    } catch (err: any) {
      callback?.({ success: false, error: err.message });
    }
  });

  // ─── Chat Message ────────────────────────────────────────────────────────
  socket.on("game:chat", (data: { gameId: string; message: string }) => {
    io.to(`game:${data.gameId}`).emit("game:chat", {
      userId,
      message: data.message,
      timestamp: new Date().toISOString(),
    });
  });

  // ─── Disconnect ──────────────────────────────────────────────────────────
  socket.on("disconnect", () => {
    clearClockInterval(socket);
    logger.info(`Socket disconnected: ${userId}`);
  });
}

// ─── Clock Management ────────────────────────────────────────────────────────

const clockIntervals = new Map<string, NodeJS.Timeout>();

function startClockForGame(io: Server, gameId: string): void {
  if (clockIntervals.has(gameId)) return;

  const interval = setInterval(async () => {
    const clocks = await GameService.getClock(gameId);
    if (clocks) {
      io.to(`game:${gameId}`).emit("game:clock", clocks);
    }
  }, CLOCK_INTERVAL);

  clockIntervals.set(gameId, interval);
}

function stopClockForGame(gameId: string): void {
  const interval = clockIntervals.get(gameId);
  if (interval) {
    clearInterval(interval);
    clockIntervals.delete(gameId);
  }
}

function clearClockInterval(socket: AuthenticatedSocket): void {
  // Individual socket cleanup — intervals are game-level
}
