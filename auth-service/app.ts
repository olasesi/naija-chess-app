import express from "express";
import helmet from "helmet";
import cors from "cors";
import cookieParser from "cookie-parser";
import morgan from "morgan";
import { env } from "./src/config/env";
import { connectDB, disconnectDB } from "./src/config/db";
import { redis } from "./src/config/redis";
import { generalRateLimiter } from "./src/middlewares/rate-limit";
import { sendError } from "./src/utils/response";
import { logger } from "./src/utils/logger";
import authRoutes from "./src/routes/auth.routes";

const app = express();

// ─── Security Middleware ──────────────────────────────────────────────────────
app.use(helmet());
app.use(
  cors({
    origin: env.CLIENT_URL,
    credentials: true, // Required for cookies
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
  })
);

// ─── General Middleware ───────────────────────────────────────────────────────
app.use(express.json({ limit: "10kb" })); // Prevent large payload attacks
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());
app.use(morgan(env.NODE_ENV === "production" ? "combined" : "dev"));
app.use(generalRateLimiter);

// Trust proxy (needed when behind NGINX/load balancer for real IP)
app.set("trust proxy", 1);

// ─── Routes ───────────────────────────────────────────────────────────────────
app.use("/api/auth", authRoutes);

// Health check — used by Kubernetes liveness/readiness probes
app.get("/health", (_req, res) => {
  res.json({
    status: "ok",
    service: "auth-service",
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
    logger.info(`🚀 Auth service running on port ${PORT} [${env.NODE_ENV}]`);
  });

  // Graceful shutdown — important for Kubernetes rolling deploys
  const shutdown = async (signal: string) => {
    logger.info(`${signal} received — shutting down gracefully`);
    server.close(async () => {
      await disconnectDB();
      await redis.quit();
      logger.info("Auth service shut down");
      process.exit(0);
    });
  };

  process.on("SIGTERM", () => shutdown("SIGTERM"));
  process.on("SIGINT", () => shutdown("SIGINT"));
}

start().catch((err) => {
  logger.error("Failed to start auth service:", err);
  process.exit(1);
});

export default app;
