'use client';

import type { ArchitectureConsultingPayload } from '@/types/chat';

interface BlueprintStrategicIntelligenceProps {
  consulting: ArchitectureConsultingPayload | null;
}

export default function BlueprintStrategicIntelligence({
  consulting,
}: BlueprintStrategicIntelligenceProps) {
  if (!consulting) return null;

  const org = consulting.organizational_intelligence;
  const lifecycle = consulting.lifecycle_intelligence;
  const cost = consulting.cost_evolution;
  const ecosystem = consulting.ecosystem_evolution;
  const calibration = consulting.confidence_calibration;
  const simReason = consulting.simulation_reasoning;

  const hasContent =
    org?.insights?.length ||
    lifecycle?.notes?.length ||
    cost?.trajectories?.length ||
    ecosystem?.insights?.length ||
    calibration?.explanation ||
    simReason?.organizational_note;

  if (!hasContent) return null;

  return (
    <details className="shrink-0 border-b border-[var(--border-subtle)] bg-[var(--surface-secondary)]/25 px-4 py-2 md:px-5">
      <summary className="cursor-pointer text-[10px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
        Strategic intelligence
      </summary>
      <div className="mt-2 space-y-3 pb-2 text-xs text-[var(--text-secondary)]">
        {calibration && (
          <section>
            <p className="font-medium text-[var(--foreground)]">{calibration.headline}</p>
            <p className="mt-0.5">{calibration.explanation}</p>
            {calibration.uncertainty_zones?.map((z) => (
              <p key={z} className="mt-1 italic text-[var(--text-muted)]">
                · {z}
              </p>
            ))}
          </section>
        )}
        {simReason?.organizational_note && (
          <p>
            <span className="font-medium text-[var(--foreground)]">Simulation · </span>
            {simReason.organizational_note}
          </p>
        )}
        {org?.insights?.map((line) => (
          <p key={line}>
            <span className="font-medium text-[var(--foreground)]">Organization · </span>
            {line}
          </p>
        ))}
        {lifecycle?.notes?.map((line) => (
          <p key={line}>
            <span className="font-medium text-[var(--foreground)]">Lifecycle · </span>
            {line}
          </p>
        ))}
        {cost?.trajectories?.map((t) => (
          <p key={t.title}>
            <span className="font-medium text-[var(--foreground)]">{t.title} · </span>
            {t.insight}
          </p>
        ))}
        {ecosystem?.insights?.map((line) => (
          <p key={line}>
            <span className="font-medium text-[var(--foreground)]">Ecosystem · </span>
            {line}
          </p>
        ))}
      </div>
    </details>
  );
}
