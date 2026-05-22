import { env } from "./env";

export interface RouteConfig {
  path: string;
  target: string;
  auth: boolean;
  publicPaths?: string[];  // sub-paths that don't require auth
}

// Routes that should bypass JWT verification (auth service handles its own)
const AUTH_PUBLIC_PATHS = [
  "/api/auth/register",
  "/api/auth/login",
  "/api/auth/google",
  "/api/auth/refresh",
];

export const routes: RouteConfig[] = [
  {
    path: "/api/auth",
    target: env.AUTH_SERVICE_URL,
    auth: false,  // auth service manages its own auth
    publicPaths: AUTH_PUBLIC_PATHS,
  },
  {
    path: "/api/users",
    target: env.USER_SERVICE_URL,
    auth: true,
    // Django user-service on :8000
  },
  {
    path: "/api/games",
    target: env.GAME_SERVICE_URL,
    auth: true,
  },
  {
    path: "/api/ratings",
    target: env.RATING_SERVICE_URL,
    auth: true,
  },
];
