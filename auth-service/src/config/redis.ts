import Redis from "ioredis";
import { env } from "./env";

export const redis = new Redis({
  host: env.REDIS_HOST,
  port: parseInt(env.REDIS_PORT),
  password: env.REDIS_PASSWORD,
  retryStrategy: (times) => {
    // Retry with exponential backoff, max 30s
    const delay = Math.min(times * 500, 30000);
    return delay;
  },
  maxRetriesPerRequest: 3,
});

redis.on("connect", () => console.log("✅ Redis connected"));
redis.on("error", (err) => console.error("❌ Redis error:", err));

// Key helpers — centralised so keys are never mistyped across services
export const RedisKeys = {
  refreshToken: (token: string) => `refresh_token:${token}`,
  blacklistedToken: (jti: string) => `blacklisted:${jti}`,
  loginAttempts: (ip: string) => `login_attempts:${ip}`,
  passwordReset: (token: string) => `pwd_reset:${token}`,
  emailVerification: (token: string) => `email_verify:${token}`,
};
