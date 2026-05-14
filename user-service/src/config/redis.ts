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

redis.on("connect", () => console.log("Redis connected [user-service]"));
redis.on("error", (err) => console.error("Redis error [user-service]:", err));

export const RedisKeys = {
  userOnline: (userId: string) => `online:${userId}`,
  userSearch: (query: string) => `search:${query}`,
};
