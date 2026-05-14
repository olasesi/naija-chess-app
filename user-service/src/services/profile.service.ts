import fs from "fs/promises";
import path from "path";
import { prisma } from "../config/db";
import { env } from "../config/env";
import { logger } from "../utils/logger";

export interface UserProfilePublic {
  userId: string;
  displayName: string | null;
  bio: string | null;
  avatar: string | null;
  country: string | null;
  title: string | null;
  createdAt: Date;
}

export const ProfileService = {
  async getOrCreateProfile(userId: string): Promise<UserProfilePublic> {
    let profile = await prisma.userProfile.findUnique({ where: { userId } });

    if (!profile) {
      profile = await prisma.userProfile.create({
        data: { userId },
      });
      logger.info(`Profile created for user: ${userId}`);
    }

    return this._toPublic(profile);
  },

  async updateProfile(
    userId: string,
    data: {
      displayName?: string;
      bio?: string;
      country?: string;
      title?: string;
    }
  ): Promise<UserProfilePublic> {
    await this.getOrCreateProfile(userId);

    const profile = await prisma.userProfile.update({
      where: { userId },
      data,
    });

    logger.info(`Profile updated for user: ${userId}`);
    return this._toPublic(profile);
  },

  async uploadAvatar(
    userId: string,
    file: Express.Multer.File
  ): Promise<UserProfilePublic> {
    await this.getOrCreateProfile(userId);

    // Get old avatar to delete it
    const current = await prisma.userProfile.findUnique({ where: { userId } });
    const oldAvatar = current?.avatar;

    const avatarUrl = `/uploads/${file.filename}`;

    const profile = await prisma.userProfile.update({
      where: { userId },
      data: { avatar: avatarUrl },
    });

    // Delete old avatar file
    if (oldAvatar) {
      const oldPath = path.join(env.UPLOAD_DIR, path.basename(oldAvatar));
      try {
        await fs.unlink(oldPath);
      } catch {
        // File might not exist — that's fine
      }
    }

    logger.info(`Avatar uploaded for user: ${userId}`);
    return this._toPublic(profile);
  },

  async searchProfiles(query: string, limit = 20): Promise<UserProfilePublic[]> {
    const profiles = await prisma.userProfile.findMany({
      where: {
        OR: [
          { displayName: { contains: query } },
          { userId: { contains: query } },
        ],
      },
      take: limit,
      orderBy: { updatedAt: "desc" },
    });
    return profiles.map(this._toPublic);
  },

  async getProfileByUserId(userId: string): Promise<UserProfilePublic | null> {
    const profile = await prisma.userProfile.findUnique({ where: { userId } });
    return profile ? this._toPublic(profile) : null;
  },

  _toPublic(profile: any): UserProfilePublic {
    return {
      userId: profile.userId,
      displayName: profile.displayName,
      bio: profile.bio,
      avatar: profile.avatar,
      country: profile.country,
      title: profile.title,
      createdAt: profile.createdAt,
    };
  },
};
