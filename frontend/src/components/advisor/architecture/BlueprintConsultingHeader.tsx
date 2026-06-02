'use client';

import type { BlueprintConsultingSummary } from '@/lib/architectureBlueprintNarrative';
import BlueprintWorkspaceToolbar from './BlueprintWorkspaceToolbar';

type ViewMode = 'simple' | 'technical';

interface BlueprintConsultingHeaderProps {
  summary: BlueprintConsultingSummary;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  onFit: () => void;
  onReset: () => void;
}

function ConfidenceBadge({
  headline,
  subline,
  evidence,
  tone,
}: {
  headline: string;
  subline: string;
  evidence: string[];
  tone: BlueprintConsultingSummary['confidenceTone'];
}) {
  const toneClass =
    tone === 'high'
      ? 'border-[var(--accent)]/30 bg-[var(--accent-muted)] text-[var(--accent)]'
      : tone === 'solid'
        ? 'border-[var(--border-subtle)] bg-[var(--surface-secondary)] text-[var(--foreground)]'
        : 'border-[var(--border-subtle)] bg-[var(--surface-panel)] text-[var(--text-secondary)]';

  return (
    <div className={`rounded-xl border px-3 py-2 ${toneClass}`}>
      <p className="text-xs font-semibold">{headline}</p>
      <p className="mt-0.5 text-[11px] leading-snug opacity-90">{subline}</p>
      {evidence.length > 0 && (
        <ul className="mt-2 space-y-0.5 text-[10px] leading-snug opacity-85">
          {evidence.map((item) => (
            <li key={item}>· {item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function BlueprintConsultingHeader({
  summary,
  viewMode,
  onViewModeChange,
  onFit,
  onReset,
}: BlueprintConsultingHeaderProps) {
  return (
    <header className="blueprint-consulting-header shrink-0 border-b border-[var(--border-subtle)] bg-[var(--surface-panel)] px-4 py-4 md:px-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1 space-y-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              {summary.workloadLabel && (
                <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-[var(--accent)]">
                  {summary.workloadLabel}
                </p>
              )}
              {summary.scaleBadge && (
                <span className="rounded-full border border-[var(--border-subtle)] bg-[var(--surface-secondary)] px-2 py-0.5 text-[10px] font-medium text-[var(--text-secondary)]">
                  {summary.scaleBadge}
                </span>
              )}
              {summary.operationalComplexity && (
                <span className="rounded-full border border-[var(--border-subtle)] bg-[var(--surface-secondary)] px-2 py-0.5 text-[10px] font-medium text-[var(--text-muted)]">
                  {summary.operationalComplexity}
                </span>
              )}
            </div>
            <h2 className="mt-1 text-xl font-semibold tracking-tight text-[var(--foreground)] md:text-2xl">
              {summary.title}
            </h2>
            {summary.continuityFraming && (
              <p className="mt-1 text-xs font-medium text-[var(--accent)]">
                {summary.continuityFraming}
              </p>
            )}
            <p className="mt-2 max-w-3xl text-sm leading-relaxed text-[var(--text-secondary)]">
              {summary.subtitle}
            </p>
            {summary.strongestEvidence && (
              <p className="mt-2 max-w-3xl text-xs leading-relaxed text-[var(--text-muted)]">
                <span className="font-medium text-[var(--text-secondary)]">
                  Strongest alignment ·{' '}
                </span>
                {summary.strongestEvidence}
              </p>
            )}
            {summary.comparativePriorityLine &&
              !summary.subtitle.includes(summary.comparativePriorityLine) && (
                <p className="mt-2 max-w-3xl text-sm font-medium text-[var(--foreground)]">
                  {summary.comparativePriorityLine}
                </p>
              )}
          </div>

          {summary.priorities.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                This architecture prioritizes
              </p>
              <ul className="mt-2 flex flex-wrap gap-2">
                {summary.priorities.map((item) => (
                  <li
                    key={item}
                    className="rounded-full border border-[var(--border-subtle)] bg-[var(--surface-secondary)] px-3 py-1 text-xs text-[var(--text-secondary)]"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {(summary.deploymentRationale || summary.scalingRationale) && (
            <div className="grid gap-2 text-xs text-[var(--text-muted)] sm:grid-cols-2">
              {summary.deploymentRationale && (
                <p>
                  <span className="font-medium text-[var(--text-secondary)]">Deployment · </span>
                  {summary.deploymentRationale}
                </p>
              )}
              {summary.scalingRationale && (
                <p>
                  <span className="font-medium text-[var(--text-secondary)]">Scale · </span>
                  {summary.scalingRationale}
                </p>
              )}
            </div>
          )}

          <p className="text-xs text-[var(--text-muted)]">{summary.trustLine}</p>
        </div>

        <div className="flex shrink-0 flex-col gap-2 sm:flex-row lg:flex-col lg:items-end">
          <ConfidenceBadge
            headline={summary.confidenceHeadline}
            subline={summary.confidenceSubline}
            evidence={
              summary.evidenceItems.length > 0
                ? summary.evidenceItems.map((e) => `${e.label}: ${e.detail}`)
                : summary.confidenceEvidence
            }
            tone={summary.confidenceTone}
          />
          <div className="hidden lg:block">
            <BlueprintWorkspaceToolbar />
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            <div
              className="flex rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-secondary)] p-0.5"
              role="group"
              aria-label="View mode"
            >
              {(
                [
                  { id: 'simple' as ViewMode, label: 'Simple' },
                  { id: 'technical' as ViewMode, label: 'Technical' },
                ] as const
              ).map(({ id, label }) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => onViewModeChange(id)}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium transition ${
                    viewMode === id
                      ? 'bg-[var(--surface-panel)] text-[var(--foreground)] shadow-[var(--shadow-soft)]'
                      : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            <button
              type="button"
              onClick={onFit}
              className="rounded-md border border-[var(--border-subtle)] px-2.5 py-1 text-xs font-medium text-[var(--text-secondary)] hover:bg-[var(--surface-hover)]"
            >
              Fit
            </button>
            <button
              type="button"
              onClick={onReset}
              className="rounded-md border border-[var(--border-subtle)] px-2.5 py-1 text-xs font-medium text-[var(--text-secondary)] hover:bg-[var(--surface-hover)]"
            >
              Reset
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
