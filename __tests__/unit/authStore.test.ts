import { act } from '@testing-library/react-native';

import { useAuthStore } from '@/stores/authStore';

const mockUser = {
  id: '1',
  email: 'test@example.com',
  name: 'Test User',
};

const mockToken = 'mock-token-123';

describe('useAuthStore', () => {
  beforeEach(() => {
    // Reset store state between tests
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });
  });

  it('should initialize with unauthenticated state', () => {
    const { user, token, isAuthenticated } = useAuthStore.getState();
    expect(user).toBeNull();
    expect(token).toBeNull();
    expect(isAuthenticated).toBe(false);
  });

  it('should set user and token on login', () => {
    act(() => {
      useAuthStore.getState().login(mockUser, mockToken);
    });

    const { user, token, isAuthenticated } = useAuthStore.getState();
    expect(user).toEqual(mockUser);
    expect(token).toBe(mockToken);
    expect(isAuthenticated).toBe(true);
  });

  it('should clear state on logout', () => {
    act(() => {
      useAuthStore.getState().login(mockUser, mockToken);
      useAuthStore.getState().logout();
    });

    const { user, token, isAuthenticated } = useAuthStore.getState();
    expect(user).toBeNull();
    expect(token).toBeNull();
    expect(isAuthenticated).toBe(false);
  });

  it('should update loading state', () => {
    act(() => {
      useAuthStore.getState().setLoading(true);
    });
    expect(useAuthStore.getState().isLoading).toBe(true);

    act(() => {
      useAuthStore.getState().setLoading(false);
    });
    expect(useAuthStore.getState().isLoading).toBe(false);
  });
});
