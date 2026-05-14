import { Request, Response } from "express";
import { PreferencesService } from "../services/preferences.service";
import { sendSuccess, sendError } from "../utils/response";

export const PreferencesController = {
  async getPreferences(req: Request, res: Response): Promise<void> {
    try {
      const userId = req.user!.sub;
      const preferences = await PreferencesService.getOrCreatePreferences(userId);
      sendSuccess(res, { preferences });
    } catch (err: any) {
      sendError(res, err.message || "Failed to get preferences", 500);
    }
  },

  async updatePreferences(req: Request, res: Response): Promise<void> {
    try {
      const userId = req.user!.sub;
      const preferences = await PreferencesService.updatePreferences(userId, req.body);
      sendSuccess(res, { preferences }, "Preferences updated");
    } catch (err: any) {
      sendError(res, err.message || "Failed to update preferences", 500);
    }
  },
};
