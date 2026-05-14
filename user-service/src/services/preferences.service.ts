import { prisma } from "../config/db";
import { logger } from "../utils/logger";

export interface UserPreferencesPublic {
  userId: string;
  theme: string;
  boardStyle: string;
  pieceStyle: string;
  soundEnabled: boolean;
  showAnalysis: boolean;
  autoPromote: boolean;
}

export const PreferencesService = {
  async getOrCreatePreferences(userId: string): Promise<UserPreferencesPublic> {
    let prefs = await prisma.userPreference.findUnique({ where: { userId } });

    if (!prefs) {
      await prisma.userProfile.upsert({
        where: { userId },
        create: { userId },
        update: {},
      });

      prefs = await prisma.userPreference.create({
        data: { userId },
      });
    }

    return this._toPublic(prefs);
  },

  async updatePreferences(
    userId: string,
    data: Partial<{
      theme: string;
      boardStyle: string;
      pieceStyle: string;
      soundEnabled: boolean;
      showAnalysis: boolean;
      autoPromote: boolean;
    }>
  ): Promise<UserPreferencesPublic> {
    await this.getOrCreatePreferences(userId);

    const prefs = await prisma.userPreference.update({
      where: { userId },
      data,
    });

    logger.info(`Preferences updated for user: ${userId}`);
    return this._toPublic(prefs);
  },

  _toPublic(prefs: any): UserPreferencesPublic {
    return {
      userId: prefs.userId,
      theme: prefs.theme,
      boardStyle: prefs.boardStyle,
      pieceStyle: prefs.pieceStyle,
      soundEnabled: prefs.soundEnabled,
      showAnalysis: prefs.showAnalysis,
      autoPromote: prefs.autoPromote,
    };
  },
};
