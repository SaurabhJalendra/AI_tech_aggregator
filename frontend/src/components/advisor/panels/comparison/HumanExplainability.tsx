'use client';

import EntityChip from '@/components/advisor/EntityChip';
import { formatEntityLabel } from '@/lib/entityDisplay';
import {
  humanizeAppliedFilter,
  humanizeFilterReason,
} from '@/lib/consultingExplain';
import { filterUserVisibleFilters } from '@/lib/explainabilityFilters';
import { buildRecommendationNarrative } from '@/lib/recommendationNarrative';
import { parseComparisonPayload } from '@/lib/comparisonPanel';
import type { ConstraintStatePayload, RecommendationExplainPayload } from '@/types/chat';

interface HumanExplainabilityProps {
  explain: RecommendationExplainPayload | null;
  trace: Record<string, unknown> | null;
  playbookId?: string | null;
  constraintState?: ConstraintStatePayload | null;
  comparisonData?: Record<string, unknown> | null;
}

/**
 * Step 3 — human-readable consulting explanations (not raw trace dumps).
 */
export default function HumanExplainability({
  explain,
  trace,
  playbookId = null,
  constraintState = null,
  comparisonData = null,
}: HumanExplainabilityProps) {
  if (!explain && !trace) return null;

  const comparison = comparisonData ? parseComparisonPayload(comparisonData) : null;
  const narrative =
    comparison && buildRecommendationNarrative(comparison, constraintState, explain, playbookId);

  const appliedFilters = filterUserVisibleFilters(explain?.applied_filters);
  const filteredOut = filterUserVisibleFilters(
    Array.isArray(trace?.filtered_out)
      ? (trace.filtered_out as Array<{ slug: string; reason: string }>)
      : []
  );
  const reasoningSteps = explain?.reasoning_steps || [];
  const shortlist = Array.isArray(explain?.shortlist) ? (explain.shortlist as string[]) : [];

  const hasContent =
    shortlist.length > 0 ||
    appliedFilters.length > 0 ||
    filteredOut.length > 0 ||
    reasoningSteps.length > 0;

  if (!hasContent) {
    return (
      <p className="text-sm text-[var(--text-muted)]">
        The advisor applied your requirements to rank options deterministically. Open technical
        details for score breakdowns.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      {narrative && (
        <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
          {narrative.constraintLeadIn && (
            <span className="text-[var(--foreground)]">{narrative.constraintLeadIn}</span>
          )}
          {narrative.playbookFraming}
        </p>
      )}

      {shortlist.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
            Final shortlist
          </h4>
          <p className="mb-3 text-sm text-[var(--text-secondary)]">
            These options best match your workload after filtering and scoring.
          </p>
          <div className="flex flex-wrap gap-2">
            {shortlist.map((slug, i) => (
              <EntityChip key={slug} slug={slug} rank={i + 1} />
            ))}
          </div>
        </div>
      )}

      {reasoningSteps.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
            How we reached this recommendation
          </h4>
          <ul className="space-y-2">
            {reasoningSteps.map((step, i) => (
              <li
                key={i}
                className="flex gap-2 text-sm leading-relaxed text-[var(--text-secondary)]"
              >
                <span className="mt-0.5 text-[var(--text-muted)]">•</span>
                <span>{step}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {filteredOut.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
            What we ruled out
          </h4>
          <ul className="space-y-2.5">
            {filteredOut.slice(0, 6).map((f) => (
              <li
                key={f.slug}
                className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-secondary)] px-4 py-3 text-sm leading-relaxed text-[var(--text-secondary)]"
              >
                {humanizeFilterReason(f.slug, f.reason)}
              </li>
            ))}
          </ul>
        </div>
      )}

      {appliedFilters.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
            Constraint fit
          </h4>
          <ul className="space-y-2 text-sm text-[var(--text-secondary)]">
            {appliedFilters.slice(0, 4).map((f, i) => (
              <li key={`${f.slug}-${i}`}>{humanizeAppliedFilter(f.slug, f.reason)}</li>
            ))}
          </ul>
        </div>
      )}

      {explain?.scores && shortlist[0] && (
        <p className="text-sm text-[var(--text-muted)]">
          <span className="font-medium text-[var(--foreground)]">
            {formatEntityLabel(shortlist[0])}
          </span>{' '}
          leads the shortlist for your current constraints. Expand technical details to see exact
          scores.
        </p>
      )}
    </div>
  );
}
