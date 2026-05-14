import { Router } from "express";
import { StatsController } from "../controllers/stats.controller";
import { authenticate } from "../middlewares/auth.middleware";
import { validate } from "../middlewares/validate";
import { z } from "zod";

const router = Router();

const recordResultSchema = z.object({
  result: z.enum(["win", "loss", "draw"]),
  timeControl: z.enum(["bullet", "blitz", "rapid", "classical"]),
  opponentRating: z.number().int().min(0).max(4000),
});

router.get("/me", authenticate, StatsController.getStats);
router.get("/:userId", authenticate, StatsController.getStats);
router.post(
  "/record",
  authenticate,
  validate(recordResultSchema),
  StatsController.recordGameResult
);

export default router;
