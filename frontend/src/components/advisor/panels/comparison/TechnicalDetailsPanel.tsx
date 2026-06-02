'use client';

import { useState } from 'react';
import EntityChip from '@/components/advisor/EntityChip';
import { formatEntityLabel, getEntityColor } from '@/lib/entityColors';
import RadarAdvancedView from './RadarAdvancedView';
import type { ParsedComparison } from '@/lib/comparisonPanel';
import type { RecommendationExplainPayload } from '@/types/chat';

interface TechnicalDetailsPanelProps {
  comparison: ParsedComparison;
  explain: RecommendationExplainPayload | null;
  trace: Record<string, unknown> | null;
}

/**
 * Step 4 — raw traces, score matrices, pipeline internals (not primary eye-line).
 */
export default function TechnicalDetailsPanel({
  comparison,
  explain,
  trace,
}: TechnicalDetailsPanelProps) {
  const [showRadar, setShowRadar] = useState(false);
  const [showRawJson, setShowRawJson] = useState(false);

  const scoreBreakdowns = explain?.score_breakdowns || {};
  const scores = explain?.scores || {};
  const shortlistSlugs = new Set(
    Array.isArray(explain?.shortlist) ? (explain.shortlist as string[]) : []
  );

  return (
    <div className="space-y-5">
      <p className="text-xs text-[var(--text-muted)]">
        Deterministic pipeline output for engineers. Colors are session-stable; rankings follow the
        playbook shortlist.
      </p>

      {Object.keys(scores).length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
            Pipeline scores
          </h4>
          <div className="space-y-2">
            {Object.entries(scores)
              .filter(([slug]) => shortlistSlugs.size === 0 || shortlistSlugs.has(slug))
              .sort(([, a], [, b]) => Number(b) - Number(a))
              .map(([slug, total]) => {
                const breakdown = scoreBreakdowns[slug] || {};
                const color = getEntityColor(slug);
                return (
                  <div
                    key={slug}
                    className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-secondary)] p-3"
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
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {Object.entries(breakdown).map(([k, v]) => (
                          <span
                            key={k}
                            className="rounded px-2 py-0.5 font-mono text-[10px] text-[var(--text-muted)]"
                            style={{ background: 'var(--surface-panel)' }}
                          >
                            {k}: {Number(v).toFixed(1)}
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

      {Array.isArray(explain?.shortlist) && explain.shortlist.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
            Shortlist slugs
          </h4>
          <div className="flex flex-wrap gap-2">
            {(explain.shortlist as string[]).map((slug, i) => (
              <EntityChip key={slug} slug={slug} rank={i + 1} className="font-mono text-xs" />
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setShowRadar((v) => !v)}
          className="rounded-lg border border-[var(--border-subtle)] px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)] hover:bg-[var(--surface-hover)]"
        >
          {showRadar ? 'Hide' : 'Show'} radar chart
        </button>
        <button
          type="button"
          onClick={() => setShowRawJson((v) => !v)}
          className="rounded-lg border border-[var(--border-subtle)] px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)] hover:bg-[var(--surface-hover)]"
        >
          {showRawJson ? 'Hide' : 'Show'} raw trace JSON
        </button>
      </div>

      {showRadar && <RadarAdvancedView comparison={comparison} />}

      {showRawJson && (trace || explain) && (
        <pre className="scrollbar-hidden max-h-64 overflow-auto rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-secondary)] p-3 font-mono text-[10px] leading-tight text-[var(--text-secondary)]">
          {JSON.stringify({ trace, explain }, null, 2)}
        </pre>
      )}
    </div>
  );
}
