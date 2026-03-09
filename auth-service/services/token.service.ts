import jwt from "jsonwebtoken";
import { v4 as uuidv4 } from "uuid";
import { env } from "../config/env";
import { redis, RedisKeys } from "../config/redis";
import { prisma } from "../config/db";

export interface AccessTokenPayload {
  sub: string; // userId
  email: string;
  role: string;
  jti: string; // unique token id — used for blacklisting
}

export interface RefreshTokenPayload {
  sub: string;
  tokenId: string; // DB RefreshToken.id
}

export const TokenService = {
  // Generate short-lived access token (15 min)
  generateAccessToken(userId: string, email: string, role: string): string {
    const payload: AccessTokenPayload = {
      sub: userId,
      email,
      role,
      jti: uuidv4(),
    };
    return jwt.sign(payload, env.JWT_ACCESS_SECRET, {
      expiresIn: env.JWT_ACCESS_EXPIRES_IN,
    } as jwt.SignOptions);
  },

  // Generate long-lived refresh token (7 days), stored in DB + Redis
  async generateRefreshToken(
    userId: string,
    ipAddress?: string,
    userAgent?: string
  ): Promise<string> {
    const tokenId = uuidv4();
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days

    // Store in MySQL for audit trail + revocation
    const dbToken = await prisma.refreshToken.create({
      data: {
        id: tokenId,
        token: uuidv4(),
        userId,
        expiresAt,
        ipAddress,
        userAgent,
      },
    });

    const payload: RefreshTokenPayload = { sub: userId, tokenId: dbToken.id };
    const token = jwt.sign(payload, env.JWT_REFRESH_SECRET, {
      expiresIn: env.JWT_REFRESH_EXPIRES_IN,
    } as jwt.SignOptions);

    // Cache in Redis for fast lookup
    await redis.setex(
      RedisKeys.refreshToken(token),
      7 * 24 * 60 * 60,
      JSON.stringify({ userId, tokenId: dbToken.id })
    );

    return token;
  },

  verifyAccessToken(token: string): AccessTokenPayload {
    return jwt.verify(token, env.JWT_ACCESS_SECRET) as AccessTokenPayload;
  },

  verifyRefreshToken(token: string): RefreshTokenPayload {
    return jwt.verify(token, env.JWT_REFRESH_SECRET) as RefreshTokenPayload;
  },

  // Blacklist an access token (on logout) until it naturally expires
  async blacklistAccessToken(jti: string, expiresIn: number): Promise<void> {
    await redis.setex(RedisKeys.blacklistedToken(jti), expiresIn, "1");
  },

  async isAccessTokenBlacklisted(jti: string): Promise<boolean> {
    const result = await redis.get(RedisKeys.blacklistedToken(jti));
    return result !== null;
  },

  // Revoke a specific refresh token
  async revokeRefreshToken(token: string): Promise<void> {
    await redis.del(RedisKeys.refreshToken(token));

    try {
      const payload = this.verifyRefreshToken(token);
      await prisma.refreshToken.update({
        where: { id: payload.tokenId },
        data: { isRevoked: true },
      });
    } catch {
      // Token might be invalid already — that's fine
    }
  },

  // Revoke ALL refresh tokens for a user (force logout everywhere)
  async revokeAllUserTokens(userId: string): Promise<void> {
    await prisma.refreshToken.updateMany({
      where: { userId, isRevoked: false },
      data: { isRevoked: true },
    });
    // Redis tokens will expire naturally — acceptable tradeoff
  },
};
