import { Request, Response } from "express";
import { redis, RedisKeys } from "../config/redis";
import { sendSuccess, sendError } from "../utils/response";

export const MatchmakingController = {
  async queueStatus(req: Request, res: Response): Promise<void> {
    try {
      const timeControl = req.query.timeControl as string || "rapid";
      const key = RedisKeys.matchmaking(timeControl);
      const size = await redis.llen(key);
      sendSuccess(res, { queueSize: size, timeControl });
    } catch (err: any) {
      sendError(res, err.message || "Failed to get queue status", 500);
    }
  },
};
