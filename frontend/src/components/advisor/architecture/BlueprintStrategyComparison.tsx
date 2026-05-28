'use client';

import type { StrategyComparisonPayload } from '@/types/chat';
import { formatEntityLabel } from '@/lib/entityDisplay';

interface BlueprintStrategyComparisonProps {
  comparison: StrategyComparisonPayload;
  onClose?: () => void;
}

function summarizeArchitecture(arch: Record<string, unknown> | undefined): string {
  if (!arch) return '—';
  const selections = arch.selections as Record<string, string> | undefined;
  if (selections && Object.keys(selections).length > 0) {
    return Object.values(selections)
      .slice(0, 5)
      .map((slug) => formatEntityLabel(slug))
      .join(' · ');
  }
  const nodes = arch.nodes as Array<{ label?: string; slug?: string }> | undefined;
  if (nodes?.length) {
    return nodes
      .slice(0, 5)
      .map((n) => formatEntityLabel(n.slug ?? n.label ?? ''))
      .join(' · ');
  }
  return '—';
}

export default function BlueprintStrategyComparison({
  comparison,
  onClose,
}: BlueprintStrategyComparisonProps) {
  return (
    <div className="shrink-0 border-b border-[var(--accent)]/30 bg-[var(--surface-secondary)] px-4 py-4 md:px-5">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--accent)]">
            Infrastructure strategy comparison
          </p>
          <p className="mt-1 text-sm font-medium text-[var(--foreground)]">{comparison.theme}</p>
          {comparison.consulting_summary && (
            <p className="mt-1 text-xs text-[var(--text-secondary)]">{comparison.consulting_summary}</p>
          )}
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

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-panel)] p-3">
          <p className="text-[10px] font-semibold uppercase text-[var(--text-muted)]">
            {comparison.left_label}
          </p>
          <p className="mt-2 text-xs leading-relaxed text-[var(--text-secondary)]">
            {summarizeArchitecture(comparison.left_architecture)}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--accent)]/35 bg-[var(--accent-muted)]/20 p-3">
          <p className="text-[10px] font-semibold uppercase text-[var(--accent)]">
            {comparison.right_label}
          </p>
          <p className="mt-2 text-xs leading-relaxed text-[var(--text-secondary)]">
            {summarizeArchitecture(comparison.right_architecture)}
          </p>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        {comparison.dimensions.map((dim) => (
          <div
            key={dim.dimension}
            className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-panel)]/80 px-3 py-2.5"
          >
            <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
              {dim.dimension}
            </p>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              <p className="text-xs text-[var(--text-secondary)]">
                <span className="font-medium text-[var(--foreground)]">{comparison.left_label}: </span>
                {dim.left}
              </p>
              <p className="text-xs text-[var(--text-secondary)]">
                <span className="font-medium text-[var(--foreground)]">{comparison.right_label}: </span>
                {dim.right}
              </p>
            </div>
            <p className="mt-2 text-[11px] italic text-[var(--text-muted)]">{dim.insight}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
