import { create } from 'zustand';
import {
  applyResolvedTheme,
  DEFAULT_THEME_PREFERENCE,
  getSystemPrefersDark,
  persistThemePreference,
  readStoredThemePreference,
  resolveTheme,
  type ResolvedTheme,
  type ThemePreference,
} from '@/lib/theme';

interface ThemeState {
  preference: ThemePreference;
  resolved: ResolvedTheme;
  hydrated: boolean;
  initialize: () => void;
  setPreference: (preference: ThemePreference) => void;
  syncSystem: () => void;
}

function computeResolved(preference: ThemePreference): ResolvedTheme {
  return resolveTheme(preference, getSystemPrefersDark());
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  preference: DEFAULT_THEME_PREFERENCE,
  resolved: 'light',
  hydrated: false,

  initialize: () => {
    const preference = readStoredThemePreference();
    const resolved = computeResolved(preference);
    applyResolvedTheme(resolved);
    set({ preference, resolved, hydrated: true });
  },

  setPreference: (preference) => {
    persistThemePreference(preference);
    const resolved = computeResolved(preference);
    applyResolvedTheme(resolved);
    set({ preference, resolved });
  },

  syncSystem: () => {
    const { preference } = get();
    if (preference !== 'system') return;
    const resolved = computeResolved('system');
    applyResolvedTheme(resolved);
    set({ resolved });
  },
}));
