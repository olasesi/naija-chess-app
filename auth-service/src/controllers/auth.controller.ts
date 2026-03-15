import { Request, Response } from 'express';
import { AuthService } from '../services/auth.service';
import { sendSuccess, sendError } from '../utils/response';
import { logger } from '../utils/logger';

const REFRESH_COOKIE_OPTIONS = {
  httpOnly: true,           // JS cannot access — XSS protection
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'strict' as const,
  maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days in ms
};

export const AuthController = {
  async register(req: Request, res: Response): Promise<void> {
    try {
      const { email, username, password } = req.body;
      const { user, tokens } = await AuthService.register(email, username, password);

      res.cookie('refreshToken', tokens.refreshToken, REFRESH_COOKIE_OPTIONS);
      sendSuccess(res, { user, accessToken: tokens.accessToken }, 'Registration successful', 201);
    } catch (err: any) {
      const messages: Record<string, string> = {
        EMAIL_TAKEN: 'This email is already registered',
        USERNAME_TAKEN: 'This username is already taken',
      };
      sendError(res, messages[err.message] || 'Registration failed', 400);
    }
  },

  async login(req: Request, res: Response): Promise<void> {
    try {
      const { email, password } = req.body;
      const ipAddress = req.ip;
      const userAgent = req.headers['user-agent'];

      const { user, tokens } = await AuthService.login(
        email,
        password,
        ipAddress,
        userAgent
      );

      res.cookie('refreshToken', tokens.refreshToken, REFRESH_COOKIE_OPTIONS);
      sendSuccess(res, { user, accessToken: tokens.accessToken }, 'Login successful');
    } catch (err: any) {
      const messages: Record<string, string> = {
        INVALID_CREDENTIALS: 'Invalid email or password',
        ACCOUNT_DISABLED: 'Your account has been disabled',
      };
      // Always return same message for invalid credentials — prevents user enumeration
      sendError(res, messages[err.message] || 'Invalid email or password', 401);
    }
  },

  async googleAuth(req: Request, res: Response): Promise<void> {
    try {
      const { idToken } = req.body;
      const ipAddress = req.ip;
      const userAgent = req.headers['user-agent'];

      const { user, tokens, isNew } = await AuthService.googleAuth(
        idToken,
        ipAddress,
        userAgent
      );

      res.cookie('refreshToken', tokens.refreshToken, REFRESH_COOKIE_OPTIONS);
      sendSuccess(
        res,
        { user, accessToken: tokens.accessToken, isNew },
        isNew ? 'Account created successfully' : 'Login successful',
        isNew ? 201 : 200
      );
    } catch (err: any) {
      logger.error('Google OAuth error:', err);
      const messages: Record<string, string> = {
        ACCOUNT_DISABLED: 'Your account has been disabled',
      };
      sendError(res, messages[err.message] || 'Google authentication failed', 401);
    }
  },

  async refresh(req: Request, res: Response): Promise<void> {
    try {
      // Accept refresh token from HttpOnly cookie (preferred) or body (mobile)
      const refreshToken = req.cookies?.refreshToken || req.body?.refreshToken;

      if (!refreshToken) {
        sendError(res, 'Refresh token required', 401);
        return;
      }

      const tokens = await AuthService.refreshTokens(
        refreshToken,
        req.ip,
        req.headers['user-agent']
      );

      res.cookie('refreshToken', tokens.refreshToken, REFRESH_COOKIE_OPTIONS);
      sendSuccess(res, { accessToken: tokens.accessToken }, 'Token refreshed');
    } catch {
      res.clearCookie('refreshToken');
      sendError(res, 'Invalid or expired refresh token', 401);
    }
  },

  async logout(req: Request, res: Response): Promise<void> {
    try {
      const accessToken = req.headers.authorization?.split(' ')[1] || '';
      const refreshToken = req.cookies?.refreshToken || req.body?.refreshToken;

      await AuthService.logout(accessToken, refreshToken);
      res.clearCookie('refreshToken');
      sendSuccess(res, null, 'Logged out successfully');
    } catch {
      sendError(res, 'Logout failed', 500);
    }
  },

  async logoutAll(req: Request, res: Response): Promise<void> {
    try {
      const userId = req.user!.sub;
      const accessToken = req.headers.authorization?.split(' ')[1] || '';

      await AuthService.logoutAll(userId, accessToken);
      res.clearCookie('refreshToken');
      sendSuccess(res, null, 'Logged out from all devices');
    } catch {
      sendError(res, 'Logout failed', 500);
    }
  },

  async me(req: Request, res: Response): Promise<void> {
    try {
      const user = await AuthService.getMe(req.user!.sub);
      sendSuccess(res, { user });
    } catch {
      sendError(res, 'User not found', 404);
    }
  },
};