'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import {
  DIMENSION_LABELS,
  getMatrixScore,
  inferWeaknesses,
  type ParsedComparison,
} from '@/lib/comparisonPanel';
import {
  formatEntityLabel,
  getEntityColor,
  getEntityGlowColor,
  getEntityHoverColor,
  getEntityMutedColor,
} from '@/lib/entityColors';
import type { RecommendationExplainPayload } from '@/types/chat';

interface CapabilityComparisonBarsProps {
  comparison: ParsedComparison;
  emphasizedDimensions: Set<string>;
  hoveredSlug: string | null;
  onHover: (slug: string | null) => void;
  explain?: RecommendationExplainPayload | null;
  /** Hide per-bar numeric scores (advanced breakdown). */
  showScores?: boolean;
}

interface TooltipState {
  slug: string;
  dim: string;
  x: number;
  y: number;
}

function reasoningSnippet(
  explain: RecommendationExplainPayload | null | undefined,
  slug: string
): string | null {
  if (!explain?.reasoning_steps?.length) return null;
  const label = formatEntityLabel(slug);
  const match = explain.reasoning_steps.find(
    (step) =>
      step.toLowerCase().includes(slug) || step.toLowerCase().includes(label)
  );
  return match ?? explain.reasoning_steps[0] ?? null;
}

export default function CapabilityComparisonBars({
  comparison,
  emphasizedDimensions,
  hoveredSlug,
  onHover,
  explain,
  showScores = true,
}: CapabilityComparisonBarsProps) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const displayOrder = comparison.pipelineRanking;

  const strengthsBySlug = useMemo(() => {
    const map: Record<string, string[]> = {};
    for (const slug of displayOrder) {
      map[slug] = comparison.highlights[slug] || [];
    }
    return map;
  }, [comparison.highlights, displayOrder]);

  const weaknessesBySlug = useMemo(() => {
    const map: Record<string, string[]> = {};
    for (const slug of displayOrder) {
      map[slug] = inferWeaknesses(
        comparison.matrix,
        slug,
        comparison.dimensions,
        comparison.pipelineRanking
      );
    }
    return map;
  }, [comparison, displayOrder]);

  const showTooltip = useCallback((slug: string, dim: string, el: HTMLElement) => {
    const rect = el.getBoundingClientRect();
    setTooltip({
      slug,
      dim,
      x: rect.left + rect.width / 2,
      y: rect.top,
    });
  }, []);

  const tooltipData = tooltip
    ? getMatrixScore(comparison.matrix, tooltip.slug, tooltip.dim)
    : null;

  const tooltipPortal =
    mounted && tooltip && tooltipData
      ? createPortal(
          <div
            className="pointer-events-none fixed z-[100] max-w-sm -translate-x-1/2 -translate-y-full rounded-xl border px-4 py-3 text-xs backdrop-blur-sm"
            style={{
              left: tooltip.x,
              top: tooltip.y - 10,
              background: 'var(--tooltip-bg)',
              borderColor: 'var(--tooltip-border)',
              boxShadow: 'var(--shadow-elevated)',
            }}
            role="tooltip"
          >
            <p
              className="font-semibold tracking-tight"
              style={{ color: getEntityHoverColor(tooltip.slug) }}
            >
              {formatEntityLabel(tooltip.slug)}
              <span className="font-normal text-[var(--text-muted)]">
                {' '}
                · {DIMENSION_LABELS[tooltip.dim] || tooltip.dim.replace(/_/g, ' ')}
              </span>
            </p>
            <p className="mt-1.5 font-mono text-sm tabular-nums text-[var(--foreground)]">
              {tooltipData.value.toFixed(1)}
              <span className="text-[var(--text-muted)]"> / 10</span>
            </p>
            {tooltipData.justification && (
              <p className="mt-2 leading-relaxed text-[var(--text-secondary)]">
                {tooltipData.justification}
              </p>
            )}
            {strengthsBySlug[tooltip.slug]?.[0] && (
              <p className="mt-2 text-[11px] text-[var(--text-secondary)]">
                <span className="font-medium text-[var(--foreground)]">Strength · </span>
                {strengthsBySlug[tooltip.slug][0].replace(/^Strong in [^:]+:\s*/i, '')}
              </p>
            )}
            {weaknessesBySlug[tooltip.slug]?.[0] && (
              <p className="mt-1 text-[11px] text-[var(--text-muted)]">
                <span className="font-medium text-[var(--text-secondary)]">Tradeoff · </span>
                {weaknessesBySlug[tooltip.slug][0]}
              </p>
            )}
            {reasoningSnippet(explain, tooltip.slug) && (
              <p className="mt-2 border-t border-[var(--border-subtle)] pt-2 text-[11px] leading-relaxed text-[var(--text-muted)]">
                {reasoningSnippet(explain, tooltip.slug)}
              </p>
            )}
          </div>,
          document.body
        )
      : null;

  return (
    <section className="surface-panel overflow-hidden rounded-2xl">
      <div className="border-b border-[var(--border-subtle)] px-5 py-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-[var(--foreground)]">
              Ranked comparison
            </h3>
            <p className="mt-0.5 text-xs text-[var(--text-muted)]">
              One view across dimensions — hover to compare alternatives
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {displayOrder.map((slug, i) => {
              const color = getEntityColor(slug);
              const dimmed = hoveredSlug != null && hoveredSlug !== slug;
              const active = hoveredSlug === slug;
              return (
                <button
                  key={slug}
                  type="button"
                  className="inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-[11px] font-medium transition-all duration-200"
                  style={{
                    opacity: dimmed ? 0.55 : 1,
                    color: active ? getEntityHoverColor(slug) : color,
                    backgroundColor: getEntityMutedColor(slug, active ? 0.18 : 0.1),
                    borderColor: getEntityMutedColor(slug, active ? 0.28 : 0.16),
                    boxShadow: active ? `0 2px 12px ${getEntityGlowColor(slug, 0.12)}` : undefined,
                  }}
                  onMouseEnter={() => onHover(slug)}
                  onMouseLeave={() => onHover(null)}
                >
                  <span
                    className="h-2 w-2 shrink-0 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  <span className="tabular-nums text-[var(--text-muted)]">#{i + 1}</span>
                  {formatEntityLabel(slug)}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="space-y-1.5 p-5">
        {comparison.dimensions.map((dim) => {
          const label = DIMENSION_LABELS[dim] || dim.replace(/_/g, ' ');
          const emphasized = emphasizedDimensions.has(dim);

          return (
            <div
              key={dim}
              className={`rounded-xl px-3 py-3.5 transition-colors duration-200 ${
                emphasized
                  ? 'ring-1'
                  : 'hover:bg-[var(--surface-hover)]/60'
              }`}
              style={
                emphasized
                  ? {
                      background: 'var(--emphasis-warm)',
                      boxShadow: 'inset 0 0 0 1px var(--emphasis-warm-ring)',
                    }
                  : undefined
              }
            >
              <div className="mb-3 flex items-center gap-2">
                <p
                  className={`text-xs font-semibold tracking-wide ${
                    emphasized
                      ? 'text-[var(--foreground)]'
                      : 'text-[var(--text-muted)]'
                  }`}
                >
                  {label}
                </p>
                {emphasized && (
                  <span
                    className="rounded-full px-2 py-0.5 text-[10px] font-medium text-[var(--text-secondary)]"
                    style={{ background: 'var(--emphasis-warm)' }}
                  >
                    Weighted for your constraints
                  </span>
                )}
              </div>

              <div className="space-y-2.5">
                {displayOrder.map((slug) => {
                  const { value } = getMatrixScore(comparison.matrix, slug, dim);
                  const color = getEntityColor(slug);
                  const dimmed = hoveredSlug != null && hoveredSlug !== slug;
                  const highlighted = hoveredSlug === slug;
                  const pct = (value / 10) * 100;

                  return (
                    <div
                      key={`${dim}-${slug}`}
                      className={`group grid items-center gap-3 transition-opacity duration-200 ${
                        showScores ? 'grid-cols-[5.5rem_1fr_2rem]' : 'grid-cols-[5.5rem_1fr]'
                      }`}
                      style={{ opacity: dimmed ? 0.5 : 1 }}
                      onMouseEnter={() => onHover(slug)}
                      onMouseLeave={() => {
                        onHover(null);
                        setTooltip(null);
                      }}
                    >
                      <span
                        className="truncate text-right text-[11px] font-medium"
                        style={{ color: highlighted ? getEntityHoverColor(slug) : color }}
                      >
                        {formatEntityLabel(slug)}
                      </span>
                      <div
                        className="relative h-2.5 overflow-hidden rounded-full"
                        style={{ background: 'var(--track-fill)' }}
                        onMouseEnter={(e) => showTooltip(slug, dim, e.currentTarget)}
                        onMouseLeave={() => setTooltip(null)}
                      >
                        <div
                          role="meter"
                          aria-valuenow={value}
                          aria-valuemin={0}
                          aria-valuemax={10}
                          className="absolute inset-y-0 left-0 rounded-full transition-all duration-500 ease-out"
                          style={{
                            width: `${pct}%`,
                            background: `linear-gradient(90deg, ${getEntityMutedColor(slug, 0.42)} 0%, ${color} 88%)`,
                            boxShadow: highlighted
                              ? `0 0 10px ${getEntityGlowColor(slug, 0.12)}`
                              : undefined,
                          }}
                        />
                      </div>
                      {showScores && (
                        <span className="text-right font-mono text-[10px] tabular-nums text-[var(--text-muted)]">
                          {value.toFixed(1)}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {tooltipPortal}
    </section>
  );
}
