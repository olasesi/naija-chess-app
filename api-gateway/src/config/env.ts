import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
  PORT: z.string().default("3000"),

  // JWT
  JWT_ACCESS_SECRET: z.string().min(32),

  // Service URLs
  AUTH_SERVICE_URL: z.string().default("http://auth-service:3001"),
  USER_SERVICE_URL: z.string().default("http://user-service:8000"),
  GAME_SERVICE_URL: z.string().default("http://game-service:3003"),
  RATING_SERVICE_URL: z.string().default("http://rating-service:8001"),
  ANALYSIS_SERVICE_URL: z.string().default("http://analysis-service:8002"),
  CHAT_SERVICE_URL: z.string().default("http://chat-service:3004"),
  NOTIFICATION_SERVICE_URL: z.string().default("http://notification-service:8003"),
  TOURNAMENT_SERVICE_URL: z.string().default("http://tournament-service:8004"),
  FORUM_SERVICE_URL: z.string().default("http://forum-service:8005"),
  ADMIN_SERVICE_URL: z.string().default("http://admin-service:8006"),

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
