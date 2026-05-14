import { prisma } from "../config/db";
import { logger } from "../utils/logger";

export interface UserStatsPublic {
  userId: string;
  gamesPlayed: number;
  wins: number;
  losses: number;
  draws: number;
  winStreak: number;
  bestWinStreak: number;
  bulletRating: number;
  blitzRating: number;
  rapidRating: number;
  classicalRating: number;
  puzzleRating: number;
  puzzleRatingMax: number;
}

export const StatsService = {
  async getOrCreateStats(userId: string): Promise<UserStatsPublic> {
    let stats = await prisma.userStats.findUnique({ where: { userId } });

    if (!stats) {
      // Ensure profile exists first
      await prisma.userProfile.upsert({
        where: { userId },
        create: { userId },
        update: {},
      });

      stats = await prisma.userStats.create({
        data: { userId },
      });
    }

    return this._toPublic(stats);
  },

  async recordGameResult(
    userId: string,
    result: "win" | "loss" | "draw",
    timeControl: "bullet" | "blitz" | "rapid" | "classical",
    opponentRating: number
  ): Promise<UserStatsPublic> {
    const stats = await this.getOrCreateStats(userId);

    const updates: any = {
      gamesPlayed: { increment: 1 },
    };

    if (result === "win") {
      updates.wins = { increment: 1 };
      updates.winStreak = { increment: 1 };
      updates.bestWinStreak = Math.max(stats.bestWinStreak, stats.winStreak + 1);
    } else if (result === "loss") {
      updates.losses = { increment: 1 };
      updates.winStreak = 0;
    } else {
      updates.draws = { increment: 1 };
    }

    // Simple ELO-like rating update
    const ratingKey = `${timeControl}Rating` as keyof UserStatsPublic;
    const currentRating = stats[ratingKey] as number;
    const expected = 1 / (1 + Math.pow(10, (opponentRating - currentRating) / 400));
    const K = 32;
    const score = result === "win" ? 1 : result === "draw" ? 0.5 : 0;
    const newRating = Math.round(currentRating + K * (score - expected));
    updates[ratingKey] = newRating;

    const updated = await prisma.userStats.update({
      where: { userId },
      data: updates,
    });

    logger.info(`Stats updated for user ${userId}: ${result} in ${timeControl}`);
    return this._toPublic(updated);
  },

  _toPublic(stats: any): UserStatsPublic {
    return {
      userId: stats.userId,
      gamesPlayed: stats.gamesPlayed,
      wins: stats.wins,
      losses: stats.losses,
      draws: stats.draws,
      winStreak: stats.winStreak,
      bestWinStreak: stats.bestWinStreak,
      bulletRating: stats.bulletRating,
      blitzRating: stats.blitzRating,
      rapidRating: stats.rapidRating,
      classicalRating: stats.classicalRating,
      puzzleRating: stats.puzzleRating,
      puzzleRatingMax: stats.puzzleRatingMax,
    };
  },
};
