import { Router } from "express";
import { z } from "zod";
import { GameController } from "../controllers/game.controller";
import { MatchmakingController } from "../controllers/matchmaking.controller";
import { authenticate } from "../middlewares/auth.middleware";
import { validate } from "../middlewares/validate";

const router = Router();

const createGameSchema = z.object({
  timeControl: z.enum(["bullet", "blitz", "rapid", "classical"]).optional(),
  startingFen: z.string().optional(),
  username: z.string().optional(),
  rating: z.number().int().min(0).max(4000).optional(),
});

const joinGameSchema = z.object({
  username: z.string().optional(),
  rating: z.number().int().min(0).max(4000).optional(),
});

const importGameSchema = z.object({
  pgn: z.string().min(1).max(200000),
  username: z.string().optional(),
  timeControl: z.enum(["bullet", "blitz", "rapid", "classical"]).optional(),
});

// Game CRUD
router.post("/", authenticate, validate(createGameSchema), GameController.createGame);

// Library + PGN import/export (registered before param routes)
router.get("/library", authenticate, GameController.getLibrary);
router.post("/import", authenticate, validate(importGameSchema), GameController.importGame);
router.get("/:gameId/pgn", authenticate, GameController.getPgn);

router.get("/:gameId", authenticate, GameController.getGame);
router.get("/user/:userId", authenticate, GameController.getUserGames);
router.get("/user/me", authenticate, GameController.getUserGames);

// Join
router.post("/:gameId/join", authenticate, validate(joinGameSchema), GameController.joinGame);

// Actions
router.post("/:gameId/resign", authenticate, GameController.resign);
router.post("/:gameId/draw", authenticate, GameController.offerDraw);
router.post("/:gameId/draw/accept", authenticate, GameController.acceptDraw);

// Matchmaking
router.get("/matchmaking/queue", authenticate, MatchmakingController.queueStatus);

export default router;
