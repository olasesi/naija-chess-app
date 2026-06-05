import { useQuery, useMutation, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { apiClient } from '@/lib/api/client';

type ApiError = AxiosError<{ message: string; errors?: Record<string, string[]> }>;

// ── Generic GET hook ────────────────────────────────────────────────────────
export function useGet<TData>(
  key: string[],
  url: string,
  options?: Omit<UseQueryOptions<TData, ApiError>, 'queryKey' | 'queryFn'>,
) {
  return useQuery<TData, ApiError>({
    queryKey: key,
    queryFn: async () => {
      const { data } = await apiClient.get<TData>(url);
      return data;
    },
    ...options,
  });
}

// ── Generic POST/PUT/PATCH/DELETE hook ──────────────────────────────────────
export function useMutate<TData, TPayload>(
  url: string,
  method: 'post' | 'put' | 'patch' | 'delete' = 'post',
  options?: UseMutationOptions<TData, ApiError, TPayload>,
) {
  return useMutation<TData, ApiError, TPayload>({
    mutationFn: async (payload: TPayload) => {
      const { data } = await apiClient[method]<TData>(url, payload);
      return data;
    },
    ...options,
  });
}
