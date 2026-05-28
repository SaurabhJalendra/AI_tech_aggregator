'use client';

import { ARCHITECTURE_STAGES } from '@/lib/architectureStages';

interface BlueprintFlowLegendProps {
  activeStageId?: string | null;
  flowPulseStageId?: string | null;
  stageIdsPresent: string[];
}

export default function BlueprintFlowLegend({
  activeStageId,
  flowPulseStageId,
  stageIdsPresent,
}: BlueprintFlowLegendProps) {
  const stages = ARCHITECTURE_STAGES.filter((s) => stageIdsPresent.includes(s.id));

  if (stages.length === 0) return null;

  return (
    <div
      className="flex flex-wrap items-center gap-1 border-b border-[var(--border-subtle)] bg-[var(--surface-secondary)]/60 px-4 py-2"
      aria-label="Pipeline flow"
    >
      <span className="mr-2 text-[11px] font-medium text-[var(--text-muted)]">Data flow</span>
      {stages.map((stage, i) => (
        <span key={stage.id} className="flex items-center gap-1">
          <span
            className={`rounded-md px-2 py-0.5 text-[11px] font-medium transition-colors ${
              activeStageId === stage.id
                ? 'bg-[var(--accent-muted)] text-[var(--accent)]'
                : flowPulseStageId === stage.id
                  ? 'bg-[var(--surface-secondary)] text-[var(--accent)] blueprint-flow-pulse'
                  : 'text-[var(--text-secondary)]'
            }`}
          >
            {stage.shortLabel}
          </span>
          {i < stages.length - 1 && (
            <svg
              className="h-3 w-3 text-[var(--text-muted)]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
              aria-hidden
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          )}
        </span>
      ))}
      <span className="ml-auto hidden text-[11px] text-[var(--text-muted)] sm:inline">
        Left → right follows how data moves through the system
      </span>
    </div>
  );
}
