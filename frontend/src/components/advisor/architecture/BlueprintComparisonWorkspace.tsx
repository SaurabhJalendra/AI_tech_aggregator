'use client';

import type { ArchitectureComparisonBaseline } from '@/types/chat';
import { formatEntityLabel } from '@/lib/entityDisplay';

interface BlueprintComparisonWorkspaceProps {
  baseline: ArchitectureComparisonBaseline;
  currentTitle: string;
  onClose?: () => void;
}

export default function BlueprintComparisonWorkspace({
  baseline,
  currentTitle,
  onClose,
}: BlueprintComparisonWorkspaceProps) {
  const baselineLabels = baseline.nodes
    .slice(0, 6)
    .map((n) => formatEntityLabel(n.slug ?? n.label))
    .join(' · ');

  return (
    <div className="shrink-0 border-b border-[var(--border-subtle)] bg-[var(--surface-secondary)] px-4 py-3 md:px-5">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--accent)]">
            Architecture comparison
          </p>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">
            Strategy comparison — not a feature matrix. See how operational posture shifts.
          </p>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="text-xs text-[var(--text-muted)] hover:text-[var(--foreground)]"
          >
            Hide
          </button>
        )}
      </div>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-panel)] p-3 opacity-80">
          <p className="text-[10px] font-semibold uppercase text-[var(--text-muted)]">Before</p>
          <p className="mt-1 text-sm font-medium text-[var(--foreground)]">
            {baseline.title || 'Previous architecture'}
          </p>
          <p className="mt-2 line-clamp-3 text-xs text-[var(--text-muted)]">{baselineLabels}</p>
        </div>
        <div className="rounded-lg border border-[var(--accent)]/35 bg-[var(--accent-muted)]/25 p-3">
          <p className="text-[10px] font-semibold uppercase text-[var(--accent)]">After (simulated)</p>
          <p className="mt-1 text-sm font-medium text-[var(--foreground)]">{currentTitle}</p>
          <p className="mt-2 text-xs text-[var(--text-secondary)]">
            Updated blueprint reflects re-scored components for the simulated scenario.
          </p>
        </div>
      </div>
    </div>
  );
}
