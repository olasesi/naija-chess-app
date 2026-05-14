import { Request, Response } from "express";
import { StatsService } from "../services/stats.service";
import { sendSuccess, sendError } from "../utils/response";

export const StatsController = {
  async getStats(req: Request, res: Response): Promise<void> {
    try {
      const userId = req.params.userId || req.user!.sub;
      const stats = await StatsService.getOrCreateStats(userId);
      sendSuccess(res, { stats });
    } catch (err: any) {
      sendError(res, err.message || "Failed to get stats", 500);
    }
  },

  async recordGameResult(req: Request, res: Response): Promise<void> {
    try {
      const userId = req.user!.sub;
      const { result, timeControl, opponentRating } = req.body;

      const stats = await StatsService.recordGameResult(
        userId,
        result,
        timeControl,
        opponentRating
      );
      sendSuccess(res, { stats }, "Game result recorded");
    } catch (err: any) {
      sendError(res, err.message || "Failed to record game result", 500);
    }
  },
};
