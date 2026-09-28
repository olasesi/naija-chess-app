import Redis from "ioredis";
import { env } from "./env";

export const redis = new Redis({
  host: env.REDIS_HOST,
  port: parseInt(env.REDIS_PORT),
  password: env.REDIS_PASSWORD,
  retryStrategy: (times) => {
    const delay = Math.min(times * 500, 30000);
    return delay;
  },
  maxRetriesPerRequest: 3,
});

redis.on("connect", () => console.log("Redis connected [game-service]"));
redis.on("error", (err) => console.error("Redis error [game-service]:", err));

export const RedisKeys = {
  activeGame: (gameId: string) => `game:active:${gameId}`,
  userGame: (userId: string) => `game:user:${userId}`,
  clockTick: (gameId: string) => `game:clock:${gameId}`,
  matchmaking: (timeControl: string) => `mm:queue:${timeControl}`,
};
