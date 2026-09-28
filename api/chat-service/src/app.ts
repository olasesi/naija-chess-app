import express from "express";
import { createServer } from "http";
import helmet from "helmet";
import cors from "cors";
import morgan from "morgan";
import rateLimit from "express-rate-limit";
import { env } from "./config/env";
import { connectDB, disconnectDB } from "./config/db";
import { redis } from "./config/redis";
import { initSocket } from "./socket";
import { sendError } from "./utils/response";
import { logger } from "./utils/logger";
import chatRoutes from "./routes/chat.routes";

const app = express();
const httpServer = createServer(app);

app.use(helmet());
app.use(
  cors({
    origin: env.CLIENT_URL,
    credentials: true,
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
  })
);

app.use(express.json({ limit: "10kb" }));
app.use(morgan(env.NODE_ENV === "production" ? "combined" : "dev"));

app.set("trust proxy", 1);

const limiter = rateLimit({
  windowMs: 60 * 1000,
  max: 200,
  standardHeaders: true,
  legacyHeaders: false,
  message: { success: false, message: "Too many requests, please try again later." },
});
app.use(limiter);

app.use("/api/chat", chatRoutes);

app.get("/health", (_req, res) => {
  res.json({
    status: "ok",
    service: "chat-service",
    timestamp: new Date().toISOString(),
  });
});

app.use((_req, res) => {
  sendError(res, "Route not found", 404);
});

const PORT = parseInt(env.PORT, 10);

async function start(): Promise<void> {
  await connectDB();

  if (redis.status !== "ready") {
    logger.warn("Redis not available, chat will work without presence/typing");
  }

  initSocket(httpServer);

  httpServer.listen(PORT, () => {
    logger.info(`Chat service listening on port ${PORT}`);
  });
}

function shutdown(): void {
  logger.info("Shutting down chat service...");
  httpServer.close(async () => {
    await disconnectDB();
    redis.disconnect();
    process.exit(0);
  });
}

process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);

start().catch((err) => {
  logger.error("Failed to start chat service:", err);
  process.exit(1);
});

export default app;
