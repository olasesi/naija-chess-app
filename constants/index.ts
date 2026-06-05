import Constants from 'expo-constants';

export const APP_NAME = Constants.expoConfig?.name ?? 'MyApp';
export const APP_VERSION = Constants.expoConfig?.version ?? '1.0.0';
export const IS_DEV = __DEV__;

export const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'https://api.example.com';
export const SENTRY_DSN = process.env.EXPO_PUBLIC_SENTRY_DSN ?? '';

/** Query key factory — prevents string typos in query keys */
export const QUERY_KEYS = {
  user: (id?: string) => ['user', id].filter(Boolean),
  posts: () => ['posts'],
  post: (id: string) => ['post', id],
} as const;

/** App-level timeouts & limits */
export const LIMITS = {
  API_TIMEOUT_MS: 15_000,
  MAX_UPLOAD_SIZE_MB: 10,
  TOAST_DURATION_MS: 3_000,
} as const;
