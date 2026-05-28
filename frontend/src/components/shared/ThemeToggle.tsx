'use client';

import { useThemeStore } from '@/stores/themeStore';
import type { ThemePreference } from '@/lib/theme';

const OPTIONS: { value: ThemePreference; label: string }[] = [
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
  { value: 'system', label: 'System' },
];

export default function ThemeToggle() {
  const preference = useThemeStore((s) => s.preference);
  const hydrated = useThemeStore((s) => s.hydrated);
  const setPreference = useThemeStore((s) => s.setPreference);

  return (
    <div
      className="flex items-center rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-secondary)] p-0.5"
      role="group"
      aria-label="Theme"
    >
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          type="button"
          disabled={!hydrated}
          onClick={() => setPreference(opt.value)}
          className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
            preference === opt.value
              ? 'bg-[var(--surface-panel)] text-[var(--foreground)] shadow-[var(--shadow-soft)]'
              : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
          }`}
          aria-pressed={preference === opt.value}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
