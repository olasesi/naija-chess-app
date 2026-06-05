import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";
import { env } from "../config/env";
import { sendError } from "../utils/response";

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
    next();
  } catch (err: any) {
    sendError(res, err.name === "TokenExpiredError" ? "Access token expired" : "Invalid access token", 401);
  }
};
