// ── API Response wrapper ────────────────────────────────────────────────────
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    page: number;
    perPage: number;
    total: number;
    totalPages: number;
  };
}

// ── Navigation ──────────────────────────────────────────────────────────────
// Expo Router uses file-based routing; extend as needed
export type RootRoutes = '/' | '/explore' | '/settings' | '/profile';

// ── Theme ───────────────────────────────────────────────────────────────────
export type ColorScheme = 'light' | 'dark';

// ── Environment variables ───────────────────────────────────────────────────
declare global {
  namespace NodeJS {
    interface ProcessEnv {
      EXPO_PUBLIC_API_URL: string;
      EXPO_PUBLIC_SENTRY_DSN: string;
    }
  }
}
