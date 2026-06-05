import * as Sentry from '@sentry/react-native';
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

import { storage } from '@/lib/utils/storage';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'https://api.example.com';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 15_000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// ── Request interceptor: attach auth token ──────────────────────────────────
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = storage.getString('auth.token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error),
);

// ── Response interceptor: global error handling ─────────────────────────────
apiClient.interceptors.response.use(
  response => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Handle token expiry – clear token and redirect
      storage.delete('auth.token');
      // You can emit an event or use a navigation ref here
    }

    // Capture non-network errors to Sentry
    if (error.response) {
      Sentry.captureException(error, {
        extra: {
          url: error.config?.url,
          status: error.response.status,
          data: error.response.data,
        },
      });
    }

    return Promise.reject(error);
  },
);
