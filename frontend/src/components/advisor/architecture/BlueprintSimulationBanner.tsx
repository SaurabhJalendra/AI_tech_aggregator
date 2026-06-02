'use client';

interface BlueprintSimulationBannerProps {
  label: string;
  narrative: string;
}

export default function BlueprintSimulationBanner({
  label,
  narrative,
}: BlueprintSimulationBannerProps) {
  return (
    <div className="shrink-0 border-b border-[var(--accent)]/30 bg-[var(--accent-muted)]/30 px-4 py-2.5 md:px-5">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-[var(--accent)]">
        Scenario simulation · {label}
      </p>
      <p className="mt-1 text-sm text-[var(--text-secondary)]">{narrative}</p>
    </div>
  );
}
