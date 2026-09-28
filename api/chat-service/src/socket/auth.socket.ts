import { Socket } from "socket.io";
import jwt from "jsonwebtoken";
import { env } from "../config/env";
import { AccessTokenPayload } from "../middlewares/auth.middleware";

export interface AuthenticatedSocket extends Socket {
  userId?: string;
  userEmail?: string;
  userRole?: string;
}

export function authenticateSocket(
  socket: AuthenticatedSocket,
  next: (err?: Error) => void
): void {
  const token = socket.handshake.auth?.token || socket.handshake.query?.token;

  if (!token) {
    return next(new Error("Access token required"));
  }

  try {
    const payload = jwt.verify(
      token as string,
      env.JWT_ACCESS_SECRET
    ) as AccessTokenPayload;

    socket.userId = payload.sub;
    socket.userEmail = payload.email;
    socket.userRole = payload.role;
    next();
  } catch (err: any) {
    next(new Error(err.name === "TokenExpiredError" ? "Token expired" : "Invalid token"));
  }
}
