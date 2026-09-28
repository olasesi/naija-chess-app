import bcrypt from "bcrypt";
import { v4 as uuidv4 } from "uuid";
import { prisma } from "../config/db";
import { env } from "../config/env";
import { TokenService } from "./token.service";
import { OAuthService } from "./oauth.service";
import { logger } from "../utils/logger";

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export interface UserPublic {
  id: string;
  email: string;
  username: string;
  avatar: string | null;
  role: string;
  isVerified: boolean;
  rating: number;
}

export const AuthService = {
  // ─── Register ────────────────────────────────────────────────────────────────
  async register(
    email: string,
    username: string,
    password: string
  ): Promise<{ user: UserPublic; tokens: AuthTokens }> {
    // Check duplicates
    const existing = await prisma.user.findFirst({
      where: { OR: [{ email }, { username }] },
    });

    if (existing) {
      if (existing.email === email) throw new Error("EMAIL_TAKEN");
      throw new Error("USERNAME_TAKEN");
    }

    const passwordHash = await bcrypt.hash(
      password,
      parseInt(env.BCRYPT_ROUNDS)
    );

    const user = await prisma.user.create({
      data: {
        email,
        username,
        passwordHash,
        isVerified: false,
      },
    });

    const tokens = await this._issueTokens(user.id, user.email, user.role);
    logger.info(`New user registered: ${user.email}`);

    return { user: this._toPublic(user), tokens };
  },

  // ─── Login ───────────────────────────────────────────────────────────────────
  async login(
    email: string,
    password: string,
    ipAddress?: string,
    userAgent?: string
  ): Promise<{ user: UserPublic; tokens: AuthTokens }> {
    const user = await prisma.user.findUnique({ where: { email } });

    if (!user || !user.passwordHash) {
      throw new Error("INVALID_CREDENTIALS");
    }

    if (!user.isActive) {
      throw new Error("ACCOUNT_DISABLED");
    }

    const passwordValid = await bcrypt.compare(password, user.passwordHash);
    if (!passwordValid) {
      throw new Error("INVALID_CREDENTIALS");
    }

    // Update last login
    await prisma.user.update({
      where: { id: user.id },
      data: { lastLoginAt: new Date() },
    });

    const tokens = await this._issueTokens(
      user.id,
      user.email,
      user.role,
      ipAddress,
      userAgent
    );
    logger.info(`User logged in: ${user.email}`);

    return { user: this._toPublic(user), tokens };
  },

  // ─── Google OAuth ─────────────────────────────────────────────────────────
  async googleAuth(
    idToken: string,
    ipAddress?: string,
    userAgent?: string
  ): Promise<{ user: UserPublic; tokens: AuthTokens; isNew: boolean }> {
    const googleUser = await OAuthService.verifyGoogleToken(idToken);

    // Find existing user by googleId or email
    let user = await prisma.user.findFirst({
      where: {
        OR: [{ googleId: googleUser.googleId }, { email: googleUser.email }],
      },
    });

    let isNew = false;

    if (!user) {
      // New user via Google — create account
      const username = await this._generateUniqueUsername(googleUser.name);
      user = await prisma.user.create({
        data: {
          email: googleUser.email,
          username,
          googleId: googleUser.googleId,
          avatar: googleUser.avatar,
          isVerified: googleUser.isVerified,
        },
      });
      isNew = true;
      logger.info(`New user via Google OAuth: ${user.email}`);
    } else if (!user.googleId) {
      // Existing email user connecting Google for first time
      user = await prisma.user.update({
        where: { id: user.id },
        data: {
          googleId: googleUser.googleId,
          avatar: user.avatar || googleUser.avatar,
          isVerified: true,
        },
      });
    }

    if (!user.isActive) throw new Error("ACCOUNT_DISABLED");

    await prisma.user.update({
      where: { id: user.id },
      data: { lastLoginAt: new Date() },
    });

    const tokens = await this._issueTokens(
      user.id,
      user.email,
      user.role,
      ipAddress,
      userAgent
    );

    return { user: this._toPublic(user), tokens, isNew };
  },

  // ─── Refresh Token ────────────────────────────────────────────────────────
  async refreshTokens(
    refreshToken: string,
    ipAddress?: string,
    userAgent?: string
  ): Promise<AuthTokens> {
    // Verify the JWT
    let payload;
    try {
      payload = TokenService.verifyRefreshToken(refreshToken);
    } catch {
      throw new Error("INVALID_REFRESH_TOKEN");
    }

    // Check DB — was it revoked?
    const dbToken = await prisma.refreshToken.findUnique({
      where: { id: payload.tokenId },
      include: { user: true },
    });

    if (!dbToken || dbToken.isRevoked || dbToken.expiresAt < new Date()) {
      // Potential token reuse attack — revoke all tokens for this user
      if (dbToken) {
        await TokenService.revokeAllUserTokens(dbToken.userId);
        logger.warn(`Token reuse detected for user: ${dbToken.userId}`);
      }
      throw new Error("INVALID_REFRESH_TOKEN");
    }

    if (!dbToken.user.isActive) throw new Error("ACCOUNT_DISABLED");

    // Rotate: revoke old token, issue new pair
    await TokenService.revokeRefreshToken(refreshToken);
    return this._issueTokens(
      dbToken.user.id,
      dbToken.user.email,
      dbToken.user.role,
      ipAddress,
      userAgent
    );
  },

  // ─── Logout ───────────────────────────────────────────────────────────────
  async logout(accessToken: string, refreshToken?: string): Promise<void> {
    try {
      const payload = TokenService.verifyAccessToken(accessToken);
      // Blacklist the access token for its remaining TTL
      const decoded = payload as any;
      const exp = decoded.exp as number;
      const ttl = exp - Math.floor(Date.now() / 1000);
      if (ttl > 0) {
        await TokenService.blacklistAccessToken(payload.jti, ttl);
      }
    } catch {
      // Token already invalid — that's fine
    }

    if (refreshToken) {
      await TokenService.revokeRefreshToken(refreshToken);
    }
  },

  // ─── Logout All Devices ───────────────────────────────────────────────────
  async logoutAll(userId: string, accessToken: string): Promise<void> {
    await this.logout(accessToken);
    await TokenService.revokeAllUserTokens(userId);
    logger.info(`User logged out from all devices: ${userId}`);
  },

  // ─── Get Current User ─────────────────────────────────────────────────────
  async getMe(userId: string): Promise<UserPublic> {
    const user = await prisma.user.findUnique({ where: { id: userId } });
    if (!user) throw new Error("USER_NOT_FOUND");
    return this._toPublic(user);
  },

  // ─── Helpers ──────────────────────────────────────────────────────────────
  async _issueTokens(
    userId: string,
    email: string,
    role: string,
    ipAddress?: string,
    userAgent?: string
  ): Promise<AuthTokens> {
    const [accessToken, refreshToken] = await Promise.all([
      TokenService.generateAccessToken(userId, email, role),
      TokenService.generateRefreshToken(userId, ipAddress, userAgent),
    ]);
    return { accessToken, refreshToken };
  },

  async _generateUniqueUsername(name: string): Promise<string> {
    const base = name
      .toLowerCase()
      .replace(/[^a-z0-9]/g, "")
      .slice(0, 16);
    let username = base || "player";
    let suffix = 0;
    while (await prisma.user.findUnique({ where: { username } })) {
      suffix++;
      username = `${base}${suffix}`;
    }
    return username;
  },

  _toPublic(user: any): UserPublic {
    return {
      id: user.id,
      email: user.email,
      username: user.username,
      avatar: user.avatar,
      role: user.role,
      isVerified: user.isVerified,
      rating: user.rating,
    };
  },
};
