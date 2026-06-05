import { Server as HTTPServer } from "http";
import { Server } from "socket.io";
import { env } from "../config/env";
import { logger } from "../utils/logger";
import { authenticateSocket, AuthenticatedSocket } from "./auth.socket";
import { registerChatHandlers } from "./chat.handler";

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

  io.use(authenticateSocket);

  io.on("connection", (rawSocket) => {
    const socket = rawSocket as AuthenticatedSocket;
    logger.info(`Chat socket connected: ${socket.userId} (${socket.id})`);

    registerChatHandlers(io, socket);

    socket.on("disconnect", (reason) => {
      logger.info(`Chat socket disconnected: ${socket.userId} (reason: ${reason})`);
    });
  });

  logger.info("Chat Socket.IO initialized");
  return io;
}

export function getIO(): Server {
  if (!io) throw new Error("Chat Socket.IO not initialized");
  return io;
}
