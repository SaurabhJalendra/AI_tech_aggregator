'use client';

import { useState } from 'react';
import EntityChip from '@/components/advisor/EntityChip';
import { formatEntityLabel, getEntityColor } from '@/lib/entityColors';
import { filterUserVisibleFilters } from '@/lib/explainabilityFilters';
import type { RecommendationExplainPayload } from '@/types/chat';

interface ExplainabilityDrawerProps {
  explain: RecommendationExplainPayload | null;
  trace: Record<string, unknown> | null;
}

export default function ExplainabilityDrawer({
  explain,
  trace,
}: ExplainabilityDrawerProps) {
  const [open, setOpen] = useState(false);

  if (!explain && !trace) return null;

  const appliedFilters = filterUserVisibleFilters(explain?.applied_filters);
  const filteredOut = filterUserVisibleFilters(
    Array.isArray(trace?.filtered_out)
      ? (trace.filtered_out as Array<{ slug: string; reason: string }>)
      : [],
  );
  const shortlistSlugs = new Set(
    Array.isArray(explain?.shortlist) ? (explain.shortlist as string[]) : [],
  );
  const reasoningSteps = explain?.reasoning_steps || [];
  const scoreBreakdowns = explain?.score_breakdowns || {};
  const scores = explain?.scores || {};
  const rawConstraints =
    explain?.constraint_slots ??
    (explain as { constraints?: Record<string, unknown> } | null)?.constraints ??
    (trace?.constraint_snapshot as Record<string, unknown> | undefined);
  const constraintEntries =
    rawConstraints && typeof rawConstraints === 'object' && !Array.isArray(rawConstraints)
      ? Object.entries(rawConstraints)
      : [];

  return (
    <div className="border-t border-[var(--border-subtle)]">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-1 py-3 text-sm font-medium text-[var(--text-secondary)] transition-colors hover:text-[var(--foreground)]"
      >
        <span>Why this recommendation?</span>
        <svg
          className={`h-4 w-4 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="space-y-5 pb-4">
          {Array.isArray(explain?.shortlist) && explain.shortlist.length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                Deterministic shortlist
              </h4>
              <div className="flex flex-wrap gap-2">
                {(explain.shortlist as string[]).map((slug, i) => (
                  <EntityChip key={slug} slug={slug} rank={i + 1} />
                ))}
              </div>
            </div>
          )}

          {appliedFilters.length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                Applied filters
              </h4>
              <ul className="space-y-2">
                {appliedFilters.map((f, i) => (
                  <li
                    key={`${f.slug}-${i}`}
                    className="surface-muted rounded-lg px-3 py-2 text-sm"
                  >
                    <span className="font-medium text-[var(--foreground)]">{f.slug}</span>
                    <span className="text-[var(--text-muted)]"> — {f.reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {filteredOut.length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                Removed candidates
              </h4>
              <ul className="space-y-1.5 text-sm text-[var(--text-secondary)]">
                {filteredOut.slice(0, 8).map((f) => (
                  <li key={f.slug}>
                    <span className="font-medium text-[var(--foreground)]">
                      {formatEntityLabel(f.slug)}
                    </span>
                    : {f.reason}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {Object.keys(scores).length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                Pipeline score breakdown
              </h4>
              <div className="space-y-3">
                {Object.entries(scores)
                  .filter(([slug]) => shortlistSlugs.size === 0 || shortlistSlugs.has(slug))
                  .sort(([, a], [, b]) => Number(b) - Number(a))
                  .map(([slug, total]) => {
                    const breakdown = scoreBreakdowns[slug] || {};
                    const color = getEntityColor(slug);
                    return (
                      <div
                        key={slug}
                        className="surface-muted rounded-lg p-3"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-semibold" style={{ color }}>
                            {formatEntityLabel(slug)}
                          </span>
                          <span className="font-mono text-sm tabular-nums text-[var(--foreground)]">
                            {Number(total).toFixed(2)}/10
                          </span>
                        </div>
                        {Object.keys(breakdown).length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-2">
                            {Object.entries(breakdown).map(([k, v]) => (
                              <span
                                key={k}
                                className="rounded px-2 py-0.5 text-[10px] text-[var(--text-secondary)]"
                                style={{ background: 'var(--surface-hover)' }}
                              >
                                {k.replace(/_/g, ' ')}: {Number(v).toFixed(1)}/10
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
              </div>
            </div>
          )}

          {reasoningSteps.length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                Reasoning steps
              </h4>
              <ol className="list-decimal space-y-1.5 pl-5 text-sm text-[var(--text-secondary)]">
                {reasoningSteps.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </div>
          )}

          {constraintEntries.length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                Active constraints
              </h4>
              <div className="flex flex-wrap gap-2">
                {constraintEntries.map(([k, v]) => (
                  <span
                    key={k}
                    className="rounded-full px-2.5 py-1 text-xs text-[var(--text-secondary)]"
                    style={{ background: 'var(--surface-secondary)' }}
                  >
                    {k}: {String(v)}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
