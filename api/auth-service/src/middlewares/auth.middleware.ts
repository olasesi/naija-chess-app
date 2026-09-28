import { Request, Response, NextFunction } from 'express';
import { TokenService, AccessTokenPayload } from '../services/token.service';
import { sendError } from '../utils/response';

// Extend Express Request to carry user info
declare global {
  namespace Express {
    interface Request {
      user?: AccessTokenPayload;
    }
  }
}

export const authenticate = async (
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> => {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    sendError(res, 'Access token required', 401);
    return;
  }

  const token = authHeader.split(' ')[1];

  try {
    const payload = TokenService.verifyAccessToken(token);

    // Check if token was blacklisted (logged out)
    const blacklisted = await TokenService.isAccessTokenBlacklisted(payload.jti);
    if (blacklisted) {
      sendError(res, 'Token has been revoked', 401);
      return;
    }

    req.user = payload;
    next();
  } catch (err: any) {
    if (err.name === 'TokenExpiredError') {
      sendError(res, 'Access token expired', 401);
    } else {
      sendError(res, 'Invalid access token', 401);
    }
  }
};

// Role-based access control middleware
export const authorize = (...roles: string[]) =>
  (req: Request, res: Response, next: NextFunction): void => {
    if (!req.user) {
      sendError(res, 'Unauthorized', 401);
      return;
    }

    if (!roles.includes(req.user.role)) {
      sendError(res, 'Forbidden: insufficient permissions', 403);
      return;
    }

    next();
  };