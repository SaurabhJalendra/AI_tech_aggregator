'use client';

import { useEffect } from 'react';
import { useThemeStore } from '@/stores/themeStore';

export default function ThemeProvider({ children }: { children: React.ReactNode }) {
  const initialize = useThemeStore((s) => s.initialize);
  const syncSystem = useThemeStore((s) => s.syncSystem);
  const preference = useThemeStore((s) => s.preference);

  useEffect(() => {
    initialize();
  }, [initialize]);

  useEffect(() => {
    if (preference !== 'system') return undefined;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => syncSystem();
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [preference, syncSystem]);

  return children;
}
