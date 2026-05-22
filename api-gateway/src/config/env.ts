import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
  PORT: z.string().default("3000"),

  // JWT
  JWT_ACCESS_SECRET: z.string().min(32),

  // Service URLs
  AUTH_SERVICE_URL: z.string().default("http://auth-service:3001"),
  USER_SERVICE_URL: z.string().default("http://user-service:3002"),
  GAME_SERVICE_URL: z.string().default("http://game-service:3003"),
  RATING_SERVICE_URL: z.string().default("http://rating-service:8001"),

  // App
  CLIENT_URL: z.string().default("http://localhost:5173"),
});

const parsed = envSchema.safeParse(process.env);

if (!parsed.success) {
  console.error("Invalid environment variables:");
  console.error(parsed.error.flatten().fieldErrors);
  process.exit(1);
}

export const env = parsed.data;
