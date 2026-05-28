'use client';

import { useEffect, useMemo, useState } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { useVisualIdentityStore } from '@/stores/visualIdentityStore';
import {
  deriveEmphasizedDimensions,
  parseComparisonPayload,
  withPipelineRanking,
} from '@/lib/comparisonPanel';
import RecommendationHero from './comparison/RecommendationHero';
import StackedRankingView from './comparison/StackedRankingView';
import TradeoffSpectrum from './comparison/TradeoffSpectrum';
import CapabilityComparisonBars from './comparison/CapabilityComparisonBars';
import ConsultingExpandable from './comparison/ConsultingExpandable';
import HumanExplainability from './comparison/HumanExplainability';
import TechnicalDetailsPanel from './comparison/TechnicalDetailsPanel';

interface ComparisonDecisionSurfaceProps {
  data: Record<string, unknown>;
}

type DisclosureKey = 'compare' | 'why' | 'technical';

/**
 * Phase 3A.2 — calm consulting surface with hero dominance + progressive depth.
 */
export default function ComparisonDecisionSurface({
  data,
}: ComparisonDecisionSurfaceProps) {
  const [expanded, setExpanded] = useState<Set<DisclosureKey>>(new Set());
  const [showDimensionBreakdown, setShowDimensionBreakdown] = useState(false);
  const [hoveredSlug, setHoveredSlug] = useState<string | null>(null);

  const sessionId = useChatStore((s) => s.sessionId);
  const explain = useChatStore((s) => s.lastRecommendationExplain);
  const trace = useChatStore((s) => s.lastAdvisorTrace);
  const constraintState = useChatStore((s) => s.constraintState);
  const activePlaybookId = useChatStore((s) => s.activePlaybookId);

  const bindSession = useVisualIdentityStore((s) => s.bindSession);
  const ensureEntities = useVisualIdentityStore((s) => s.ensureEntities);

  const comparison = useMemo(() => {
    const parsed = parseComparisonPayload(data);
    return parsed ? withPipelineRanking(parsed, explain) : null;
  }, [data, explain]);

  useEffect(() => {
    bindSession(sessionId);
  }, [sessionId, bindSession]);

  useEffect(() => {
    if (!comparison) return;
    ensureEntities(comparison.modules, comparison.pipelineRanking);
  }, [comparison, ensureEntities]);

  const emphasizedDimensions = useMemo(
    () =>
      comparison
        ? deriveEmphasizedDimensions(comparison.weights, constraintState, explain)
        : new Set<string>(),
    [comparison, constraintState, explain]
  );

  const toggle = (key: DisclosureKey) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const openCompare = () => setExpanded((prev) => new Set(prev).add('compare'));
  const openWhy = () => setExpanded((prev) => new Set(prev).add('why'));

  if (!comparison || comparison.pipelineRanking.length === 0) {
    return (
      <div className="flex h-96 items-center justify-center p-6">
        <p className="text-[var(--text-muted)]">No comparison data available</p>
      </div>
    );
  }

  return (
    <div className="consulting-workspace mx-auto max-w-3xl px-6 pb-16 pt-10">
      <div className="consulting-hero-zone mb-14">
        <RecommendationHero
          comparison={comparison}
          showShortlist={false}
          onCompareAlternatives={openCompare}
          onExplainWhy={openWhy}
          explain={explain}
          constraintState={constraintState}
          playbookId={activePlaybookId}
        />
      </div>

      <div className="consulting-secondary-zone space-y-3 opacity-95">
        <ConsultingExpandable
          step={2}
          title="Compare alternatives"
          subtitle="See how options rank and where tradeoffs differ"
          open={expanded.has('compare')}
          onToggle={() => toggle('compare')}
          subdued
        >
          <StackedRankingView
            comparison={comparison}
            hoveredSlug={hoveredSlug}
            onHover={setHoveredSlug}
          />
          <TradeoffSpectrum
            comparison={comparison}
            hoveredSlug={hoveredSlug}
            onHover={setHoveredSlug}
          />
          <div className="border-t border-[var(--border-subtle)] pt-4">
            <button
              type="button"
              onClick={() => setShowDimensionBreakdown((v) => !v)}
              className="text-xs font-medium text-[var(--text-secondary)] transition-colors hover:text-[var(--foreground)]"
            >
              {showDimensionBreakdown ? 'Hide' : 'View'} capability breakdown
            </button>
            {showDimensionBreakdown && (
              <div className="mt-4 animate-consulting-reveal">
                <CapabilityComparisonBars
                  comparison={comparison}
                  emphasizedDimensions={emphasizedDimensions}
                  hoveredSlug={hoveredSlug}
                  onHover={setHoveredSlug}
                  explain={explain}
                  showScores={false}
                />
              </div>
            )}
          </div>
        </ConsultingExpandable>

        <ConsultingExpandable
          step={3}
          title="Why this recommendation?"
          subtitle="Consulting narrative — not raw pipeline logs"
          open={expanded.has('why')}
          onToggle={() => toggle('why')}
          subdued
        >
          <HumanExplainability
            explain={explain}
            trace={trace}
            playbookId={activePlaybookId}
            constraintState={constraintState}
            comparisonData={data}
          />
        </ConsultingExpandable>

        <ConsultingExpandable
          step={4}
          title="Technical details"
          subtitle="Scores, traces, and advanced charts"
          open={expanded.has('technical')}
          onToggle={() => toggle('technical')}
          subdued
        >
          <TechnicalDetailsPanel comparison={comparison} explain={explain} trace={trace} />
        </ConsultingExpandable>
      </div>
    </div>
  );
}
