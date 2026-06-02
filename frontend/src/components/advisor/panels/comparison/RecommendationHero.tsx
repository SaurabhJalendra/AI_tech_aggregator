'use client';

import { useMemo } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { formatEntityLabel, getEntityColor, getEntityMutedColor } from '@/lib/entityColors';
import { pipelineTopPick, type ParsedComparison } from '@/lib/comparisonPanel';
import { buildRecommendationNarrative } from '@/lib/recommendationNarrative';
import type { ConstraintStatePayload, RecommendationExplainPayload } from '@/types/chat';

interface RecommendationHeroProps {
  comparison: ParsedComparison;
  hoveredSlug?: string | null;
  onHover?: (slug: string | null) => void;
  showShortlist?: boolean;
  onCompareAlternatives?: () => void;
  onExplainWhy?: () => void;
  explain?: RecommendationExplainPayload | null;
  constraintState?: ConstraintStatePayload | null;
  playbookId?: string | null;
}

export default function RecommendationHero({
  comparison,
  onCompareAlternatives,
  onExplainWhy,
  showShortlist = false,
  explain = null,
  constraintState = null,
  playbookId = null,
}: RecommendationHeroProps) {
  const storeExplain = useChatStore((s) => s.lastRecommendationExplain);
  const storeConstraints = useChatStore((s) => s.constraintState);
  const storePlaybook = useChatStore((s) => s.activePlaybookId);

  const narrative = useMemo(
    () =>
      buildRecommendationNarrative(
        comparison,
        constraintState ?? storeConstraints,
        explain ?? storeExplain,
        playbookId ?? storePlaybook
      ),
    [comparison, constraintState, storeConstraints, explain, storeExplain, playbookId, storePlaybook]
  );

  const top = pipelineTopPick(comparison);
  if (!top || !narrative) return null;

  const color = getEntityColor(top);
  const { confidence } = narrative;

  const confidenceRingClass =
    confidence.tone === 'high'
      ? 'consulting-confidence consulting-confidence--high'
      : confidence.tone === 'solid'
        ? 'consulting-confidence consulting-confidence--solid'
        : 'consulting-confidence consulting-confidence--moderate';

  return (
    <section
      className="consulting-hero animate-consulting-reveal"
      aria-label="Advisor recommendation"
    >
      <div className="consulting-hero__glow" style={{ backgroundColor: getEntityMutedColor(top, 0.12) }} />

      <p className="consulting-hero__eyebrow">Advisor recommendation</p>

      {narrative.constraintLeadIn && (
        <p className="consulting-hero__constraint-lead mt-3 text-sm leading-relaxed text-[var(--text-secondary)]">
          <span className="text-[var(--foreground)]">{narrative.constraintLeadIn}</span>
          {narrative.playbookFraming.charAt(0).toLowerCase() + narrative.playbookFraming.slice(1)}
        </p>
      )}

      {!narrative.constraintLeadIn && (
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[var(--text-secondary)]">
          {narrative.playbookFraming}
        </p>
      )}

      <div className="mt-8 flex flex-wrap items-start justify-between gap-6">
        <div className="min-w-0 flex-1">
          <h2 className="consulting-hero__title" style={{ color }}>
            {narrative.pickLabel}
          </h2>
          <p className="mt-3 max-w-xl text-base leading-relaxed text-[var(--text-secondary)]">
            {narrative.summary}
          </p>
        </div>

        <div className={`${confidenceRingClass} shrink-0`}>
          {confidence.percent != null && (
            <p className="consulting-confidence__value tabular-nums" style={{ color }}>
              {confidence.percent}%
            </p>
          )}
          <p className="consulting-confidence__headline">{confidence.headline}</p>
          <p className="consulting-confidence__subline">{confidence.subline}</p>
        </div>
      </div>

      <div className="mt-8 grid gap-6 md:grid-cols-2">
        {narrative.workloadFit && (
          <div className="consulting-hero__fit-card">
            <h3 className="consulting-hero__fit-label">Workload fit</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-[var(--text-secondary)]">
              {narrative.workloadFit}
            </p>
          </div>
        )}
        {narrative.operationalFit && (
          <div className="consulting-hero__fit-card">
            <h3 className="consulting-hero__fit-label">Operational fit</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-[var(--text-secondary)]">
              {narrative.operationalFit}
            </p>
          </div>
        )}
      </div>

      {narrative.whyThis.length > 0 && (
        <div className="mt-8">
          <h3 className="consulting-hero__fit-label">Why this choice</h3>
          <ul className="mt-3 space-y-2.5">
            {narrative.whyThis.map((line, i) => (
              <li
                key={i}
                className="flex gap-3 text-sm leading-relaxed text-[var(--text-secondary)]"
              >
                <span
                  className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full"
                  style={{ backgroundColor: color }}
                />
                {line}
              </li>
            ))}
          </ul>
        </div>
      )}

      {(narrative.tradeoffAccepted || narrative.whyNotAlternatives) && (
        <div className="mt-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-secondary)]/60 px-4 py-3">
          {narrative.tradeoffAccepted && (
            <p className="text-sm text-[var(--text-muted)]">{narrative.tradeoffAccepted}</p>
          )}
          {narrative.whyNotAlternatives && (
            <p className="mt-1 text-sm text-[var(--text-muted)]">{narrative.whyNotAlternatives}</p>
          )}
        </div>
      )}

      {(onCompareAlternatives || onExplainWhy) && (
        <div className="consulting-hero__actions mt-10 flex flex-wrap gap-3">
          {onCompareAlternatives && comparison.pipelineRanking.length > 1 && (
            <button type="button" onClick={onCompareAlternatives} className="consulting-cta-primary">
              Compare alternatives
            </button>
          )}
          {onExplainWhy && (
            <button type="button" onClick={onExplainWhy} className="consulting-cta-secondary">
              Why this recommendation?
            </button>
          )}
        </div>
      )}

      {showShortlist && comparison.pipelineRanking.length > 1 && (
        <p className="mt-4 text-xs text-[var(--text-muted)]">
          Shortlist:{' '}
          {comparison.pipelineRanking.map((s) => formatEntityLabel(s)).join(' · ')}
        </p>
      )}
    </section>
  );
}
