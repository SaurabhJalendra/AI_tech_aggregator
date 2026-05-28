'use client';

import { useEffect, useState } from 'react';

const STORAGE_KEY = 'advisor_blueprint_onboarding_dismissed';

export default function BlueprintOnboardingHint() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      const dismissed = localStorage.getItem(STORAGE_KEY);
      if (!dismissed) setVisible(true);
    } catch {
      setVisible(true);
    }
  }, []);

  if (!visible) return null;

  const dismiss = () => {
    setVisible(false);
    try {
      localStorage.setItem(STORAGE_KEY, '1');
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="pointer-events-none absolute bottom-4 left-1/2 z-20 w-[min(100%,420px)] -translate-x-1/2 px-4">
      <div className="pointer-events-auto flex items-start gap-3 rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-panel)] px-4 py-3 shadow-[var(--shadow-elevated)] blueprint-onboarding-hint">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold text-[var(--foreground)]">Explore this blueprint</p>
          <p className="mt-0.5 text-[11px] leading-snug text-[var(--text-muted)]">
            Select components to explore architecture decisions, alternatives, and integration
            guidance.
          </p>
        </div>
        <button
          type="button"
          onClick={dismiss}
          className="shrink-0 rounded-md px-2 py-1 text-[11px] font-medium text-[var(--accent)] hover:bg-[var(--surface-hover)]"
        >
          Got it
        </button>
      </div>
    </div>
  );
}
