import { Request, Response } from "express";
import { ProfileService } from "../services/profile.service";
import { sendSuccess, sendError } from "../utils/response";
import { logger } from "../utils/logger";

export const ProfileController = {
  async getProfile(req: Request, res: Response): Promise<void> {
    try {
      const userId = req.params.userId || req.user!.sub;
      const profile = await ProfileService.getOrCreateProfile(userId);
      sendSuccess(res, { profile });
    } catch (err: any) {
      sendError(res, err.message || "Failed to get profile", 500);
    }
  },

  async updateProfile(req: Request, res: Response): Promise<void> {
    try {
      const userId = req.user!.sub;
      const profile = await ProfileService.updateProfile(userId, req.body);
      sendSuccess(res, { profile }, "Profile updated");
    } catch (err: any) {
      sendError(res, err.message || "Failed to update profile", 500);
    }
  },

  async uploadAvatar(req: Request, res: Response): Promise<void> {
    try {
      const userId = req.user!.sub;

      if (!req.file) {
        sendError(res, "No file provided", 400);
        return;
      }

      const profile = await ProfileService.uploadAvatar(userId, req.file);
      sendSuccess(res, { profile }, "Avatar uploaded");
    } catch (err: any) {
      logger.error("Avatar upload error:", err);
      sendError(res, err.message || "Failed to upload avatar", 500);
    }
  },

  async searchProfiles(req: Request, res: Response): Promise<void> {
    try {
      const query = (req.query.q as string) || "";
      if (!query || query.length < 2) {
        sendError(res, "Search query must be at least 2 characters", 400);
        return;
      }

      const profiles = await ProfileService.searchProfiles(query);
      sendSuccess(res, { profiles });
    } catch (err: any) {
      sendError(res, err.message || "Search failed", 500);
    }
  },
};
