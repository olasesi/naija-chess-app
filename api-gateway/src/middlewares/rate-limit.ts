import rateLimit from "express-rate-limit";
import { sendError } from "../utils/response";

export const gatewayRateLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 200,
  standardHeaders: true,
  legacyHeaders: false,
  handler: (_req, res) => {
    sendError(res, "Too many requests. Please slow down.", 429);
  },
});
