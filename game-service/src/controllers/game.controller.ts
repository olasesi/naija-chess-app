import { Request, Response } from "express";
import { GameService } from "../services/game.service";
import { sendSuccess, sendError } from "../utils/response";

export const GameController = {
  async createGame(req: Request, res: Response): Promise<void> {
    try {
      const { timeControl, startingFen } = req.body;
      const player = {
        userId: req.user!.sub,
        username: req.body.username || req.user!.email,
        rating: req.body.rating || 1200,
      };
      const game = await GameService.createGame(player, timeControl, startingFen);
      sendSuccess(res, { game }, "Game created", 201);
    } catch (err: any) {
      sendError(res, err.message || "Failed to create game", 500);
    }
  },

  async getGame(req: Request, res: Response): Promise<void> {
    try {
      const game = await GameService.getGame(req.params.gameId);
      if (!game) {
        sendError(res, "Game not found", 404);
        return;
      }
      sendSuccess(res, { game });
    } catch (err: any) {
      sendError(res, err.message || "Failed to get game", 500);
    }
  },

  async getUserGames(req: Request, res: Response): Promise<void> {
    try {
      const userId = req.params.userId || req.user!.sub;
      const status = req.query.status as string | undefined;
      const limit = parseInt(req.query.limit as string) || 20;
      const skip = parseInt(req.query.skip as string) || 0;

      const result = await GameService.getUserGames(userId, status, limit, skip);
      sendSuccess(res, result);
    } catch (err: any) {
      sendError(res, err.message || "Failed to get games", 500);
    }
  },

  async joinGame(req: Request, res: Response): Promise<void> {
    try {
      const player = {
        userId: req.user!.sub,
        username: req.body.username || req.user!.email,
        rating: req.body.rating || 1200,
      };
      const game = await GameService.joinGame(req.params.gameId, player);
      sendSuccess(res, { game }, "Joined game");
    } catch (err: any) {
      const messages: Record<string, string> = {
        GAME_NOT_FOUND: "Game not found",
        GAME_NOT_AVAILABLE: "Game is not available",
        ALREADY_IN_GAME: "You are already in this game",
      };
      const status = err.message === "GAME_NOT_FOUND" ? 404 : 400;
      sendError(res, messages[err.message] || "Failed to join game", status);
    }
  },

  async resign(req: Request, res: Response): Promise<void> {
    try {
      const game = await GameService.resign(req.params.gameId, req.user!.sub);
      sendSuccess(res, { game }, "Resigned");
    } catch (err: any) {
      sendError(res, err.message || "Failed to resign", 500);
    }
  },

  async offerDraw(req: Request, res: Response): Promise<void> {
    try {
      const game = await GameService.offerDraw(req.params.gameId, req.user!.sub);
      sendSuccess(res, { game }, "Draw offered");
    } catch (err: any) {
      sendError(res, err.message || "Failed to offer draw", 500);
    }
  },

  async acceptDraw(req: Request, res: Response): Promise<void> {
    try {
      const game = await GameService.acceptDraw(req.params.gameId, req.user!.sub);
      sendSuccess(res, { game }, "Draw accepted");
    } catch (err: any) {
      sendError(res, err.message || "Failed to accept draw", 500);
    }
  },
};
