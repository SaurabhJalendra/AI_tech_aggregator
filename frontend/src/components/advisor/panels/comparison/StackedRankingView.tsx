'use client';

import { formatEntityLabel, getEntityColor, getEntityMutedColor } from '@/lib/entityColors';
import { matchConfidencePercent, pipelineTopPick, type ParsedComparison } from '@/lib/comparisonPanel';

interface StackedRankingViewProps {
  comparison: ParsedComparison;
  hoveredSlug: string | null;
  onHover: (slug: string | null) => void;
}

/**
 * Primary comparison visualization — ranked dominance without metric grid noise.
 */
export default function StackedRankingView({
  comparison,
  hoveredSlug,
  onHover,
}: StackedRankingViewProps) {
  const order = comparison.pipelineRanking;
  const top = pipelineTopPick(comparison);
  if (order.length === 0) return null;

  const scores = order.map((slug) => comparison.pipelineScores[slug] ?? 5);
  const maxScore = Math.max(...scores, 1);
  const topConfidence = top ? matchConfidencePercent(comparison.pipelineScores, top) : null;

  return (
    <section className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--surface-panel)] p-6">
      <div className="mb-5">
        <h3 className="text-sm font-semibold text-[var(--foreground)]">Ranked alternatives</h3>
        <p className="mt-1 text-xs leading-relaxed text-[var(--text-muted)]">
          One clear ordering from the advisor pipeline
          {topConfidence != null ? ` · ${topConfidence}% separation at the top` : ''}.
        </p>
      </div>

      <div className="space-y-3">
        {order.map((slug, index) => {
          const score = comparison.pipelineScores[slug] ?? 5;
          const widthPct = Math.max(28, (score / maxScore) * 100);
          const color = getEntityColor(slug);
          const isTop = index === 0;
          const dimmed = hoveredSlug != null && hoveredSlug !== slug;
          const active = hoveredSlug === slug;

          return (
            <button
              key={slug}
              type="button"
              className="group block w-full text-left transition-opacity duration-200"
              style={{ opacity: dimmed ? 0.45 : 1 }}
              onMouseEnter={() => onHover(slug)}
              onMouseLeave={() => onHover(null)}
            >
              <div className="mb-1.5 flex items-baseline justify-between gap-2">
                <span
                  className={`text-sm font-semibold ${isTop ? 'text-[var(--foreground)]' : 'text-[var(--text-secondary)]'}`}
                  style={isTop ? { color } : undefined}
                >
                  <span className="mr-2 tabular-nums text-[var(--text-muted)]">#{index + 1}</span>
                  {formatEntityLabel(slug)}
                </span>
                {isTop && (
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                    Recommended
                  </span>
                )}
              </div>
              <div
                className="h-3 overflow-hidden rounded-full transition-all duration-300"
                style={{ background: 'var(--track-fill)' }}
              >
                <div
                  className="h-full rounded-full transition-all duration-500 ease-out"
                  style={{
                    width: `${widthPct}%`,
                    background: `linear-gradient(90deg, ${getEntityMutedColor(slug, 0.35)} 0%, ${color} 100%)`,
                    boxShadow: active ? `0 0 0 1px ${getEntityMutedColor(slug, 0.4)}` : undefined,
                  }}
                />
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
