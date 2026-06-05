import { Server } from "socket.io";
import { AuthenticatedSocket } from "./auth.socket";
import { GameService } from "../services/game.service";
import { redis, RedisKeys } from "../config/redis";
import { logger } from "../utils/logger";

interface QueueEntry {
  socketId: string;
  userId: string;
  username: string;
  rating: number;
  joinedAt: number;
}

export function registerMatchmakingHandlers(io: Server, socket: AuthenticatedSocket): void {
  const userId = socket.userId!;

  socket.on("mm:join", async (data: { timeControl: string }, callback) => {
    try {
      const key = RedisKeys.matchmaking(data.timeControl || "rapid");

      // Check if already in queue
      const existing = await redis.lrange(key, 0, -1);
      for (const entry of existing) {
        const parsed: QueueEntry = JSON.parse(entry);
        if (parsed.userId === userId) {
          return callback?.({ success: false, error: "Already in queue" });
        }
      }

      const entry: QueueEntry = {
        socketId: socket.id,
        userId,
        username: socket.handshake.auth?.username || "Player",
        rating: socket.handshake.auth?.rating || 1200,
        joinedAt: Date.now(),
      };

      await redis.rpush(key, JSON.stringify(entry));
      await redis.expire(key, 300); // 5 min TTL

      socket.join(`mm:${data.timeControl}`);

      // Try to match
      await tryMatch(io, key, data.timeControl);

      const queueSize = await redis.llen(key);
      callback?.({ success: true, queueSize });
    } catch (err: any) {
      callback?.({ success: false, error: err.message });
    }
  });

  socket.on("mm:leave", async (data: { timeControl: string }, callback) => {
    try {
      const key = RedisKeys.matchmaking(data.timeControl || "rapid");
      await removeFromQueue(key, userId);
      socket.leave(`mm:${data.timeControl}`);
      callback?.({ success: true });
    } catch (err: any) {
      callback?.({ success: false, error: err.message });
    }
  });

  socket.on("disconnect", async () => {
    // Remove from all queues on disconnect
    for (const tc of ["bullet", "blitz", "rapid", "classical"]) {
      const key = RedisKeys.matchmaking(tc);
      await removeFromQueue(key, userId);
    }
  });
}

async function tryMatch(io: Server, key: string, timeControl: string): Promise<void> {
  const entries = await redis.lrange(key, 0, -1);

  if (entries.length < 2) return;

  const players: QueueEntry[] = entries.map((e) => JSON.parse(e));

  // Simple rating-based matching (first two within 200 points)
  for (let i = 0; i < players.length; i++) {
    for (let j = i + 1; j < players.length; j++) {
      const diff = Math.abs(players[i].rating - players[j].rating);
      if (diff <= 200) {
        // Match found — remove both from queue
        await removeFromQueue(key, players[i].userId);
        await removeFromQueue(key, players[j].userId);

        // Create game
        const game = await GameService.createGame(
          {
            userId: players[i].userId,
            username: players[i].username,
            rating: players[i].rating,
          },
          timeControl
        );

        const joined = await GameService.joinGame(game.gameId, {
          userId: players[j].userId,
          username: players[j].username,
          rating: players[j].rating,
        });

        // Notify both players
        io.to(players[i].socketId).emit("mm:matchFound", { game: joined });
        io.to(players[j].socketId).emit("mm:matchFound", { game: joined });

        logger.info(`Match found: ${players[i].username} vs ${players[j].username} [${timeControl}]`);
        return;
      }
    }
  }
}

async function removeFromQueue(key: string, userId: string): Promise<void> {
  const entries = await redis.lrange(key, 0, -1);
  for (const entry of entries) {
    const parsed: QueueEntry = JSON.parse(entry);
    if (parsed.userId === userId) {
      await redis.lrem(key, 1, entry);
      return;
    }
  }
}
