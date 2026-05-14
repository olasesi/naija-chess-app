import { prisma } from "../config/db";
import { logger } from "../utils/logger";

export interface FriendPublic {
  id: string;
  userId: string;
  friendId: string;
  status: string;
  createdAt: Date;
}

export const FriendsService = {
  async sendRequest(userId: string, friendId: string): Promise<FriendPublic> {
    if (userId === friendId) {
      throw new Error("CANNOT_FRIEND_SELF");
    }

    // Check existing relationship
    const existing = await prisma.friend.findFirst({
      where: {
        OR: [
          { userId, friendId },
          { userId: friendId, friendId: userId },
        ],
      },
    });

    if (existing) {
      if (existing.status === "ACCEPTED") throw new Error("ALREADY_FRIENDS");
      if (existing.status === "PENDING") throw new Error("REQUEST_ALREADY_EXISTS");
      if (existing.status === "BLOCKED") throw new Error("RELATIONSHIP_BLOCKED");
    }

    const friend = await prisma.friend.create({
      data: { userId, friendId },
    });

    logger.info(`Friend request sent: ${userId} -> ${friendId}`);
    return this._toPublic(friend);
  },

  async respondToRequest(
    userId: string,
    friendId: string,
    action: "accept" | "decline" | "block"
  ): Promise<FriendPublic> {
    const request = await prisma.friend.findFirst({
      where: { userId: friendId, friendId: userId, status: "PENDING" },
    });

    if (!request) throw new Error("REQUEST_NOT_FOUND");

    if (action === "accept") {
      const updated = await prisma.friend.update({
        where: { id: request.id },
        data: { status: "ACCEPTED" },
      });
      logger.info(`Friend request accepted: ${friendId} -> ${userId}`);
      return this._toPublic(updated);
    }

    if (action === "decline") {
      await prisma.friend.delete({ where: { id: request.id } });
      logger.info(`Friend request declined: ${friendId} -> ${userId}`);
      return { id: request.id, userId, friendId, status: "DECLINED", createdAt: request.createdAt };
    }

    // Block
    await prisma.friend.delete({ where: { id: request.id } });
    const blocked = await prisma.friend.create({
      data: { userId, friendId, status: "BLOCKED" },
    });
    logger.info(`User blocked: ${userId} -> ${friendId}`);
    return this._toPublic(blocked);
  },

  async removeFriend(userId: string, friendId: string): Promise<void> {
    await prisma.friend.deleteMany({
      where: {
        OR: [
          { userId, friendId },
          { userId: friendId, friendId: userId },
        ],
      },
    });
    logger.info(`Friend removed: ${userId} <-> ${friendId}`);
  },

  async getFriends(
    userId: string,
    status: "ACCEPTED" | "PENDING" = "ACCEPTED"
  ): Promise<FriendPublic[]> {
    const friends = await prisma.friend.findMany({
      where: {
        OR: [{ userId }, { friendId: userId }],
        status,
      },
      orderBy: { createdAt: "desc" },
    });

    return friends.map((f) => ({
      ...this._toPublic(f),
      friendId: f.userId === userId ? f.friendId : f.userId,
    }));
  },

  _toPublic(friend: any): FriendPublic {
    return {
      id: friend.id,
      userId: friend.userId,
      friendId: friend.friendId,
      status: friend.status,
      createdAt: friend.createdAt,
    };
  },
};
