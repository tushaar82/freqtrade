import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient } from '@/lib/api-client';
import { wsClient } from '@/lib/websocket-client';
import type { User, AuthState } from '@/types';

interface AuthStore extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User | null) => void;
  initializeAuth: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      loading: true,

      login: async (username: string, password: string) => {
        try {
          const response = await apiClient.login(username, password);
          const token = response.access_token;
          
          // Connect WebSocket
          wsClient.connect(token);
          
          set({
            user: { username, role: 'trader' },
            token,
            isAuthenticated: true,
            loading: false,
          });
        } catch (error) {
          console.error('Login failed:', error);
          throw error;
        }
      },

      logout: () => {
        apiClient.logout();
        wsClient.disconnect();
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          loading: false,
        });
      },

      setUser: (user: User | null) => {
        set({ user });
      },

      initializeAuth: () => {
        const token = apiClient.getToken();
        if (token) {
          wsClient.connect(token);
          set({
            token,
            isAuthenticated: true,
            loading: false,
          });
        } else {
          set({ loading: false });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
