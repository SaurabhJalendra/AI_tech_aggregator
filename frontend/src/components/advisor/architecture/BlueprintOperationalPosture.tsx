'use client';

import type { ArchitectureConsultingPayload } from '@/types/chat';

interface BlueprintOperationalPostureProps {
  posture: ArchitectureConsultingPayload['operational_posture'];
  stress?: ArchitectureConsultingPayload['operational_stress'];
}

const LABELS: Record<string, string> = {
  scaling_pressure: 'Scaling pressure',
  maintenance_complexity: 'Maintenance',
  deployment_burden: 'Deployment',
  operational_risk: 'Operational risk',
  observability_maturity: 'Observability',
  production_readiness: 'Production posture',
};

const STRESS_LABELS: Record<string, string> = {
  scaling_pressure: 'Load pressure',
  retrieval_bottleneck_risk: 'Retrieval risk',
  operational_fragility: 'Fragility',
  deployment_pressure: 'Deploy pressure',
  latency_stress: 'Latency stress',
};

export default function BlueprintOperationalPosture({
  posture,
  stress,
}: BlueprintOperationalPostureProps) {
  if (!posture && !stress) return null;

  const entries = Object.entries(posture ?? {}).filter(
    ([k, v]) => v && k !== 'consulting_note'
  );
  const stressEntries = stress
    ? Object.entries(stress).filter(
        ([k, v]) => v && k !== 'consulting_note' && STRESS_LABELS[k]
      )
    : [];
  if (entries.length === 0 && stressEntries.length === 0) return null;

  return (
    <div className="shrink-0 border-b border-[var(--border-subtle)] bg-[var(--surface-panel)]/80 px-4 py-2.5 md:px-5">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
        Operational posture
      </p>
      <div className="mt-1.5 flex flex-wrap gap-2">
        {entries.map(([key, value]) => (
          <span
            key={key}
            className={`rounded-md border px-2 py-0.5 text-[10px] ${
              key === 'operational_risk' && value === 'medium'
                ? 'border-amber-500/30 bg-amber-500/10 text-amber-800 dark:text-amber-200'
                : 'border-[var(--border-subtle)] bg-[var(--surface-secondary)] text-[var(--text-secondary)]'
            }`}
          >
            <span className="font-medium text-[var(--text-muted)]">{LABELS[key] ?? key} · </span>
            {value}
          </span>
        ))}
        {stressEntries.map(([key, value]) => (
          <span
            key={`stress-${key}`}
            className={`rounded-md border px-2 py-0.5 text-[10px] ${
              value === 'elevated'
                ? 'border-amber-500/25 bg-amber-500/8 text-amber-900/90 dark:text-amber-100/90'
                : 'border-[var(--border-subtle)] bg-[var(--surface-secondary)]/70 text-[var(--text-muted)]'
            }`}
          >
            <span className="font-medium">{STRESS_LABELS[key]} · </span>
            {value}
          </span>
        ))}
      </div>
      {stress?.consulting_note && (
        <p className="mt-1.5 text-[10px] italic text-[var(--text-muted)]">{stress.consulting_note}</p>
      )}
    </div>
  );
}
