import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";
import { env } from "../config/env";
import { sendError } from "../utils/response";
import { logger } from "../utils/logger";

export interface AccessTokenPayload {
  sub: string;
  email: string;
  role: string;
  jti: string;
}

declare global {
  namespace Express {
    interface Request {
      user?: AccessTokenPayload;
    }
  }
}

export const authenticate = (
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    sendError(res, "Access token required", 401);
    return;
  }

  const token = authHeader.split(" ")[1];

  try {
    const payload = jwt.verify(token, env.JWT_ACCESS_SECRET) as AccessTokenPayload;
    req.user = payload;

    // Forward user info to downstream services via headers
    req.headers["x-user-id"] = payload.sub;
    req.headers["x-user-email"] = payload.email;
    req.headers["x-user-role"] = payload.role;

    next();
  } catch (err: any) {
    if (err.name === "TokenExpiredError") {
      sendError(res, "Access token expired", 401);
    } else {
      sendError(res, "Invalid access token", 401);
    }
  }
};
