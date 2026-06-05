import { Server as HTTPServer } from "http";
import { Server } from "socket.io";
import { env } from "../config/env";
import { logger } from "../utils/logger";
import { authenticateSocket, AuthenticatedSocket } from "./auth.socket";
import { registerGameHandlers } from "./game.handler";
import { registerMatchmakingHandlers } from "./matchmaking.handler";

let io: Server;

export function initSocket(httpServer: HTTPServer): Server {
  io = new Server(httpServer, {
    cors: {
      origin: env.CLIENT_URL,
      credentials: true,
      methods: ["GET", "POST"],
    },
    pingInterval: 10000,
    pingTimeout: 5000,
  });

  // Authentication middleware
  io.use(authenticateSocket);

  io.on("connection", (rawSocket) => {
    const socket = rawSocket as AuthenticatedSocket;
    logger.info(`Socket connected: ${socket.userId} (${socket.id})`);

    // Register game handlers
    registerGameHandlers(io, socket);
    registerMatchmakingHandlers(io, socket);

    socket.on("disconnect", (reason) => {
      logger.info(`Socket disconnected: ${socket.userId} (reason: ${reason})`);
    });
  });

  logger.info("Socket.IO initialized");
  return io;
}

export function getIO(): Server {
  if (!io) throw new Error("Socket.IO not initialized");
  return io;
}
