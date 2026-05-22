import express from "express";
import http from "http";
import helmet from "helmet";
import cors from "cors";
import morgan from "morgan";
import { createProxyMiddleware, Options } from "http-proxy-middleware";
import { env } from "./config/env";
import { routes, RouteConfig } from "./config/routes";
import { authenticate } from "./middlewares/auth.middleware";
import { gatewayRateLimiter } from "./middlewares/rate-limit";
import { sendError } from "./utils/response";
import { logger } from "./utils/logger";

const app = express();
const httpServer = http.createServer(app);

// ─── Security Middleware ──────────────────────────────────────────────────────
app.use(helmet());
app.use(
  cors({
    origin: env.CLIENT_URL,
    credentials: true,
    methods: ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
  })
);

// ─── General Middleware ───────────────────────────────────────────────────────
app.use(express.json({ limit: "1mb" }));
app.use(morgan(env.NODE_ENV === "production" ? "combined" : "dev"));
app.use(gatewayRateLimiter);

app.set("trust proxy", 1);

// ─── Proxy Setup ──────────────────────────────────────────────────────────────
function setupProxy(route: RouteConfig): void {
  const isWebSocket = route.path === "/api/games";

  const proxyOptions: Options = {
    target: route.target,
    changeOrigin: true,
    proxyTimeout: 30000,
    timeout: 30000,
    ws: isWebSocket,  // Enable WebSocket proxying for game service (Socket.IO)

    on: {
      proxyReq: (proxyReq, req) => {
        logger.debug(`Proxying ${req.method} ${req.originalUrl} -> ${route.target}`);
      },
      proxyRes: (proxyRes, req) => {
        delete proxyRes.headers["x-powered-by"];
      },
      error: (err, req, res) => {
        logger.error(`Proxy error for ${req.originalUrl}:`, err);
        if (!res.headersSent) {
          sendError(res, "Service unavailable", 503);
        }
      },
    },
  };

  // Apply auth middleware before proxying if route requires it
  const middleware = route.auth
    ? [authenticate, createProxyMiddleware(proxyOptions)]
    : [createProxyMiddleware(proxyOptions)];

  // If route has public sub-paths, conditionally apply auth
  if (route.publicPaths && route.publicPaths.length > 0) {
    app.use(route.path, (req, res, next) => {
      const isPublic = route.publicPaths!.some((p) => req.path.startsWith(p.replace(route.path, "")));
      if (isPublic) {
        return createProxyMiddleware(proxyOptions)(req, res, next);
      }
      authenticate(req, res, () => {
        createProxyMiddleware(proxyOptions)(req, res, next);
      });
    });
  } else {
    app.use(route.path, ...middleware);
  }
}

// Register all route proxies
for (const route of routes) {
  setupProxy(route);
  logger.info(`Route registered: ${route.path} -> ${route.target}`);
}

// ─── WebSocket Upgrade (for Socket.IO / game-service) ─────────────────────────
httpServer.on("upgrade", (req, socket, head) => {
  const gameRoute = routes.find((r) => req.url?.startsWith(r.path));
  if (gameRoute) {
    const proxy = createProxyMiddleware({
      target: gameRoute.target,
      changeOrigin: true,
      ws: true,
    });
    proxy.upgrade(req, socket, head);
  } else {
    socket.destroy();
  }
});

// ─── Health Check ─────────────────────────────────────────────────────────────
app.get("/health", (_req, res) => {
  res.json({
    status: "ok",
    service: "api-gateway",
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
  httpServer.listen(PORT, () => {
    logger.info(`API Gateway running on port ${PORT} [${env.NODE_ENV}]`);
  });

  const shutdown = async (signal: string) => {
    logger.info(`${signal} received — shutting down gracefully`);
    httpServer.close(() => {
      logger.info("API Gateway shut down");
      process.exit(0);
    });
  };

  process.on("SIGTERM", () => shutdown("SIGTERM"));
  process.on("SIGINT", () => shutdown("SIGINT"));
}

start().catch((err) => {
  logger.error("Failed to start API Gateway:", err);
  process.exit(1);
});

export { app, httpServer };
