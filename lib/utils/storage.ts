import { MMKV } from 'react-native-mmkv';

export const storage = new MMKV({ id: 'app-storage' });

/** Typed helpers on top of MMKV */
export const Store = {
  get<T>(key: string): T | undefined {
    const raw = storage.getString(key);
    if (!raw) return undefined;
    try {
      return JSON.parse(raw) as T;
    } catch {
      return raw as unknown as T;
    }
  },

  set<T>(key: string, value: T): void {
    storage.set(key, JSON.stringify(value));
  },

  delete(key: string): void {
    storage.delete(key);
  },

  clear(): void {
    storage.clearAll();
  },
};
