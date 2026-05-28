'use client';

import { useBlueprintWorkspaceStore } from '@/stores/blueprintWorkspaceStore';

export default function BlueprintWorkspaceToolbar() {
  const focusMode = useBlueprintWorkspaceStore((s) => s.focusMode);
  const toggleFocusMode = useBlueprintWorkspaceStore((s) => s.toggleFocusMode);

  return (
    <button
      type="button"
      onClick={toggleFocusMode}
      className="rounded-md border border-[var(--border-subtle)] bg-[var(--surface-panel)] px-2.5 py-1 text-xs font-medium text-[var(--text-secondary)] shadow-[var(--shadow-soft)] hover:bg-[var(--surface-hover)]"
      aria-pressed={focusMode}
    >
      {focusMode ? 'Exit focus' : 'Focus workspace'}
    </button>
  );
}
