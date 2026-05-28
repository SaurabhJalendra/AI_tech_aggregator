'use client';

import {
  DEFAULT_TRADEOFF_PAIRS,
  tradeoffPosition,
  pipelineTopPick,
  type ParsedComparison,
  type TradeoffPair,
} from '@/lib/comparisonPanel';
import { tradeoffWinnerNarrative } from '@/lib/recommendationNarrative';
import {
  formatEntityLabel,
  getEntityColor,
  getEntityGlowColor,
  getEntityMutedColor,
  getEntityHoverColor,
} from '@/lib/entityColors';

interface TradeoffSpectrumProps {
  comparison: ParsedComparison;
  hoveredSlug: string | null;
  onHover: (slug: string | null) => void;
}

function SpectrumRow({
  pair,
  comparison,
  displayOrder,
  hoveredSlug,
  onHover,
}: {
  pair: TradeoffPair;
  comparison: ParsedComparison;
  displayOrder: string[];
  hoveredSlug: string | null;
  onHover: (slug: string | null) => void;
}) {
  const hasLeft = comparison.dimensions.includes(pair.leftDim);
  const hasRight = comparison.dimensions.includes(pair.rightDim);
  if (!hasLeft || !hasRight) return null;

  return (
    <div className="surface-muted rounded-xl px-4 py-4">
      <div className="mb-3 flex justify-between text-[10px] font-medium uppercase tracking-wide text-[var(--text-muted)]">
        <span>{pair.leftLabel}</span>
        <span>{pair.rightLabel}</span>
      </div>
      <div className="relative h-10">
        <div
          className="absolute left-0 right-0 top-1/2 h-px -translate-y-1/2"
          style={{ background: 'var(--border-strong)' }}
        />
        {displayOrder.map((slug) => {
          const pos = tradeoffPosition(
            comparison.matrix,
            slug,
            pair.leftDim,
            pair.rightDim
          );
          const color = getEntityColor(slug);
          const dimmed = hoveredSlug != null && hoveredSlug !== slug;
          const active = hoveredSlug === slug;
          return (
            <button
              key={`${pair.id}-${slug}`}
              type="button"
              title={formatEntityLabel(slug)}
              className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 transition-all duration-200"
              style={{
                left: `${pos * 100}%`,
                opacity: dimmed ? 0.45 : 1,
                transform: `translate(-50%, -50%) scale(${active ? 1.12 : 1})`,
              }}
              onMouseEnter={() => onHover(slug)}
              onMouseLeave={() => onHover(null)}
            >
              <span
                className="block h-3 w-3 rounded-full ring-2 ring-[var(--surface-panel)]"
                style={{
                  backgroundColor: color,
                  boxShadow: active ? `0 0 8px ${getEntityGlowColor(slug, 0.14)}` : undefined,
                }}
              />
            </button>
          );
        })}
      </div>
      <div className="mt-2 flex flex-wrap justify-center gap-2">
        {displayOrder.map((slug) => (
          <span
            key={`${pair.id}-label-${slug}`}
            className="rounded-full px-2 py-0.5 text-[10px] transition-opacity duration-200"
            style={{
              color: hoveredSlug === slug ? getEntityHoverColor(slug) : getEntityColor(slug),
              backgroundColor: getEntityMutedColor(slug, hoveredSlug === slug ? 0.16 : 0.08),
              opacity: hoveredSlug && hoveredSlug !== slug ? 0.5 : 1,
            }}
          >
            {formatEntityLabel(slug)}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function TradeoffSpectrum({
  comparison,
  hoveredSlug,
  onHover,
}: TradeoffSpectrumProps) {
  const displayOrder = comparison.pipelineRanking;
  const top = pipelineTopPick(comparison);
  const pairs = DEFAULT_TRADEOFF_PAIRS.filter(
    (p) =>
      comparison.dimensions.includes(p.leftDim) &&
      comparison.dimensions.includes(p.rightDim)
  );
  if (pairs.length === 0 || displayOrder.length < 2) return null;

  return (
    <section className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--surface-secondary)]/40 p-5">
      <h3 className="text-sm font-semibold tracking-tight text-[var(--foreground)]">
        Decision tradeoffs
      </h3>
      <p className="mt-1 mb-4 text-xs leading-relaxed text-[var(--text-muted)]">
        Where each option sits between competing goals — not a scorecard, a story.
      </p>
      {top && pairs[0] && (
        <p className="mb-4 text-sm text-[var(--text-secondary)]">
          <span className="font-medium text-[var(--foreground)]">{formatEntityLabel(top)}</span>
          {' — '}
          {tradeoffWinnerNarrative(comparison, top, pairs[0].leftDim, pairs[0].rightDim)}
        </p>
      )}
      <div className="grid gap-4 md:grid-cols-2">
        {pairs.map((pair) => (
          <SpectrumRow
            key={pair.id}
            pair={pair}
            comparison={comparison}
            displayOrder={displayOrder}
            hoveredSlug={hoveredSlug}
            onHover={onHover}
          />
        ))}
      </div>
    </section>
  );
}
