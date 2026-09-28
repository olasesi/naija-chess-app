import { Router } from "express";
import { AuthController } from "../controllers/auth.controller";
import { authenticate } from "../middlewares/auth.middleware";
import { validate } from "../middlewares/validate";
import {
  authRateLimiter,
  sensitiveRateLimiter,
} from "../middlewares/rate-limit";
import {
  registerSchema,
  loginSchema,
  googleAuthSchema,
  refreshSchema,
} from "../middlewares/validate";

const router = Router();

// ─── Public Routes ────────────────────────────────────────────────────────────
router.post(
  "/register",
  authRateLimiter,
  validate(registerSchema),
  AuthController.register
);

router.post(
  "/login",
  authRateLimiter,
  validate(loginSchema),
  AuthController.login
);

router.post(
  "/google",
  authRateLimiter,
  validate(googleAuthSchema),
  AuthController.googleAuth
);

router.post("/refresh", sensitiveRateLimiter, AuthController.refresh);

// ─── Protected Routes (require valid access token) ────────────────────────────
router.post("/logout", authenticate, AuthController.logout);
router.post("/logout-all", authenticate, AuthController.logoutAll);
router.get("/me", authenticate, AuthController.me);

export default router;
