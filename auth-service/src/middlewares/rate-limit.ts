import rateLimit from "express-rate-limit";
import { sendError } from "../utils/response";

// Strict limiter for auth endpoints (login, register)
export const authRateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 10, // 10 attempts per window
  standardHeaders: true,
  legacyHeaders: false,
  handler: (_req, res) => {
    sendError(res, "Too many attempts. Please try again in 15 minutes.", 429);
  },
});

// Looser limiter for general API endpoints
export const generalRateLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
  handler: (_req, res) => {
    sendError(res, "Too many requests. Please slow down.", 429);
  },
});

// Very strict for password reset / OTP
export const sensitiveRateLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 5,
  standardHeaders: true,
  legacyHeaders: false,
  handler: (_req, res) => {
    sendError(res, "Too many attempts. Please try again in 1 hour.", 429);
  },
});
