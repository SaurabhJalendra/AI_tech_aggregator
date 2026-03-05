import { create } from 'zustand';

export type UserTier = 'free' | 'pro' | 'enterprise';

export interface User {
  id: string;
  name: string;
  email: string;
  image?: string;
  tier: UserTier;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  tier: UserTier;
  isLoading: boolean;

  // Actions
  setUser: (user: User | null) => void;
  setTier: (tier: UserTier) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  tier: 'free',
  isLoading: true,

  setUser: (user: User | null) => {
    set({
      user,
      isAuthenticated: user !== null,
      tier: user?.tier ?? 'free',
      isLoading: false,
    });
  },

  setTier: (tier: UserTier) => {
    set({ tier });
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  },

  logout: () => {
    set({
      user: null,
      isAuthenticated: false,
      tier: 'free',
      isLoading: false,
    });
  },
}));
