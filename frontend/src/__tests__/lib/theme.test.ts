import { describe, expect, it, beforeEach } from 'vitest';
import {
  DEFAULT_THEME_PREFERENCE,
  resolveTheme,
  isThemePreference,
  THEME_STORAGE_KEY,
} from '@/lib/theme';
import { useThemeStore } from '@/stores/themeStore';

describe('theme', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: (query: string) => ({
        matches: query.includes('dark'),
        media: query,
        addEventListener: () => {},
        removeEventListener: () => {},
      }),
    });
    localStorage.clear();
    useThemeStore.setState({
      preference: DEFAULT_THEME_PREFERENCE,
      resolved: 'light',
      hydrated: false,
    });
    document.documentElement.classList.remove('dark');
    document.documentElement.dataset.theme = 'light';
  });

  it('resolves system preference from media query', () => {
    expect(resolveTheme('light', true)).toBe('light');
    expect(resolveTheme('dark', false)).toBe('dark');
    expect(resolveTheme('system', true)).toBe('dark');
    expect(resolveTheme('system', false)).toBe('light');
  });

  it('validates stored preference values', () => {
    expect(isThemePreference('light')).toBe(true);
    expect(isThemePreference('invalid')).toBe(false);
  });

  it('persists preference and applies dark class', () => {
    useThemeStore.getState().setPreference('dark');
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark');
    expect(useThemeStore.getState().resolved).toBe('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });
});
