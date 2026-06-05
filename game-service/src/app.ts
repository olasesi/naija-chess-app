import express from "express";
import { createServer } from "http";
import helmet from "helmet";
import cors from "cors";
import morgan from "morgan";
import { env } from "./config/env";
import { connectDB, disconnectDB } from "./config/db";
import { redis } from "./config/redis";
import { initSocket } from "./socket";
import { sendError } from "./utils/response";
import { logger } from "./utils/logger";
import gameRoutes from "./routes/game.routes";

const app = express();
const httpServer = createServer(app);

// ─── Security Middleware ──────────────────────────────────────────────────────
app.use(helmet());
app.use(
  cors({
    origin: env.CLIENT_URL,
    credentials: true,
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
  })
);

// ─── General Middleware ───────────────────────────────────────────────────────
app.use(express.json({ limit: "10kb" }));
app.use(morgan(env.NODE_ENV === "production" ? "combined" : "dev"));

app.set("trust proxy", 1);

// ─── Routes ───────────────────────────────────────────────────────────────────
app.use("/api/games", gameRoutes);

// Health check
app.get("/health", (_req, res) => {
  res.json({
    status: "ok",
    service: "game-service",
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

  // Initialize Socket.IO
  initSocket(httpServer);

  httpServer.listen(PORT, () => {
    logger.info(`Game service running on port ${PORT} [${env.NODE_ENV}]`);
  });

  const shutdown = async (signal: string) => {
    logger.info(`${signal} received — shutting down gracefully`);
    httpServer.close(async () => {
      await disconnectDB();
      await redis.quit();
      logger.info("Game service shut down");
      process.exit(0);
    });
  };

  process.on("SIGTERM", () => shutdown("SIGTERM"));
  process.on("SIGINT", () => shutdown("SIGINT"));
}

start().catch((err) => {
  logger.error("Failed to start game service:", err);
  process.exit(1);
});

export { app, httpServer };
