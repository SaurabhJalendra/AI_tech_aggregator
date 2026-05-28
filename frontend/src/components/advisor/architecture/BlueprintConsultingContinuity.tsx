'use client';

interface BlueprintConsultingContinuityProps {
  message: string;
}

export default function BlueprintConsultingContinuity({ message }: BlueprintConsultingContinuityProps) {
  return (
    <div
      className="shrink-0 border-b border-[var(--border-subtle)] bg-[var(--surface-panel)] px-4 py-2 md:px-5"
      role="status"
    >
      <p className="text-[11px] leading-relaxed text-[var(--text-secondary)]">
        <span className="font-semibold text-[var(--accent)]">Consulting continuity · </span>
        {message}
      </p>
    </div>
  );
}
