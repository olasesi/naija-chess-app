import express from "express";
import helmet from "helmet";
import cors from "cors";
import morgan from "morgan";
import path from "path";
import { env } from "./config/env";
import { connectDB, disconnectDB } from "./config/db";
import { redis } from "./config/redis";
import { generalRateLimiter } from "./middlewares/rate-limit";
import { sendError } from "./utils/response";
import { logger } from "./utils/logger";
import routes from "./routes/index";

const app = express();

// ─── Security Middleware ──────────────────────────────────────────────────────
app.use(helmet());
app.use(
  cors({
    origin: env.CLIENT_URL,
    credentials: true,
    methods: ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization", "X-User-Id", "X-User-Email", "X-User-Role"],
  })
);

// ─── General Middleware ───────────────────────────────────────────────────────
app.use(express.json({ limit: "10kb" }));
app.use(express.urlencoded({ extended: true }));
app.use(morgan(env.NODE_ENV === "production" ? "combined" : "dev"));
app.use(generalRateLimiter);

app.set("trust proxy", 1);

// ─── Static files (avatars) ──────────────────────────────────────────────────
app.use("/uploads", express.static(path.join(__dirname, "..", "uploads")));

// ─── Routes ───────────────────────────────────────────────────────────────────
app.use("/api/users", routes);

// Health check
app.get("/health", (_req, res) => {
  res.json({
    status: "ok",
    service: "user-service",
    timestamp: new Date().toISOString(),
  });
});

// ─── 404 Handler ──────────────────────────────────────────────────────────────
app.use((_req, res) => {
  sendError(res, "Route not found", 404);
});

// ─── Global Error Handler ─────────────────────────────────────────────────────
app.use(
  (
    err: Error,
    _req: express.Request,
    res: express.Response,
    _next: express.NextFunction
  ) => {
    logger.error("Unhandled error:", err);
    sendError(res, "Internal server error", 500);
  }
);

// ─── Start ────────────────────────────────────────────────────────────────────
const PORT = parseInt(env.PORT);

async function start() {
  await connectDB();

  const server = app.listen(PORT, () => {
    logger.info(`User service running on port ${PORT} [${env.NODE_ENV}]`);
  });

  const shutdown = async (signal: string) => {
    logger.info(`${signal} received — shutting down gracefully`);
    server.close(async () => {
      await disconnectDB();
      await redis.quit();
      logger.info("User service shut down");
      process.exit(0);
    });
  };

  process.on("SIGTERM", () => shutdown("SIGTERM"));
  process.on("SIGINT", () => shutdown("SIGINT"));
}

start().catch((err) => {
  logger.error("Failed to start user service:", err);
  process.exit(1);
});

export default app;
