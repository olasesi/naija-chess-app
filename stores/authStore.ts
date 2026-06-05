import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';

import { Store } from '@/lib/utils/storage';

interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthActions {
  login: (user: User, token: string) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState & AuthActions>()(
  immer(set => ({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,

    login: (user, token) => {
      Store.set('auth.user', user);
      Store.set('auth.token', token);
      set(state => {
        state.user = user;
        state.token = token;
        state.isAuthenticated = true;
      });
    },

    logout: () => {
      Store.delete('auth.user');
      Store.delete('auth.token');
      set(state => {
        state.user = null;
        state.token = null;
        state.isAuthenticated = false;
      });
    },

    setLoading: loading => {
      set(state => {
        state.isLoading = loading;
      });
    },

    hydrate: () => {
      const user = Store.get<User>('auth.user');
      const token = Store.get<string>('auth.token');
      if (user && token) {
        set(state => {
          state.user = user;
          state.token = token;
          state.isAuthenticated = true;
        });
      }
    },
  })),
);
