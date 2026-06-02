'use client';

import type { ArchitectureConsultingPayload } from '@/types/chat';

interface BlueprintStrategicTimelineProps {
  consulting: ArchitectureConsultingPayload | null;
}

export default function BlueprintStrategicTimeline({ consulting }: BlueprintStrategicTimelineProps) {
  const entries = consulting?.strategic_timeline ?? [];
  if (entries.length === 0) return null;

  return (
    <details className="shrink-0 border-b border-[var(--border-subtle)] px-4 py-2 md:px-5" open>
      <summary className="cursor-pointer text-[10px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
        Infrastructure strategy timeline ({entries.length})
      </summary>
      <ol className="mt-2 max-h-48 space-y-2 overflow-y-auto pb-1">
        {entries.map((entry, i) => (
          <li
            key={`${entry.type}-${entry.title}-${i}`}
            className="rounded-md border border-[var(--border-subtle)] bg-[var(--surface-panel)]/90 px-3 py-2 text-xs"
          >
            <p className="font-medium text-[var(--foreground)]">{entry.title}</p>
            <p className="mt-0.5 text-[var(--text-muted)]">{entry.detail}</p>
            {entry.at && (
              <p className="mt-1 text-[10px] text-[var(--text-muted)] opacity-80">
                {new Date(entry.at).toLocaleString()}
              </p>
            )}
          </li>
        ))}
      </ol>
    </details>
  );
}
