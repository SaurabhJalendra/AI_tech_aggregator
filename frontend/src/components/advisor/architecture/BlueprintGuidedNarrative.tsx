'use client';

import {
  activeGuidedStepIndex,
  type GuidedPipelineStep,
} from '@/lib/architectureBlueprintNarrative';

interface BlueprintGuidedNarrativeProps {
  steps: GuidedPipelineStep[];
  activeStageId: string | null;
}

export default function BlueprintGuidedNarrative({
  steps,
  activeStageId,
}: BlueprintGuidedNarrativeProps) {
  if (steps.length === 0) return null;

  const activeIdx = activeGuidedStepIndex(steps, activeStageId);

  return (
    <div
      className="blueprint-guided-narrative shrink-0 border-b border-[var(--border-subtle)] bg-[var(--surface-secondary)]/50 px-4 py-3 md:px-5"
      aria-label="How this system works"
    >
      <p className="text-[11px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
        How this system works
      </p>
      <p className="mt-1 text-xs text-[var(--text-secondary)]">
        Follow the pipeline left to right — select any component to see how it participates.
      </p>
      <ol className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {steps.map((step, idx) => {
          const isActive = activeIdx === idx;
          const isPast = activeIdx != null && idx < activeIdx;
          return (
            <li
              key={step.stageId}
              className={`rounded-lg border px-3 py-2 transition-all duration-300 ${
                isActive
                  ? 'border-[var(--accent)] bg-[var(--accent-muted)]/40 shadow-[var(--shadow-soft)]'
                  : isPast
                    ? 'border-[var(--border-subtle)] bg-[var(--surface-panel)]/80 opacity-80'
                    : 'border-[var(--border-subtle)] bg-[var(--surface-panel)]'
              }`}
            >
              <span
                className={`inline-flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${
                  isActive
                    ? 'bg-[var(--accent)] text-[var(--accent-foreground)]'
                    : 'bg-[var(--surface-secondary)] text-[var(--text-muted)]'
                }`}
              >
                {step.order}
              </span>
              <p
                className={`mt-1.5 text-xs font-semibold ${
                  isActive ? 'text-[var(--accent)]' : 'text-[var(--foreground)]'
                }`}
              >
                {step.title}
              </p>
              <p className="mt-1 line-clamp-3 text-[11px] leading-snug text-[var(--text-muted)]">
                {step.narrative}
              </p>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
