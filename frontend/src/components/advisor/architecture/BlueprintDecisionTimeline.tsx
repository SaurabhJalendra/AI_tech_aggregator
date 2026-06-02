'use client';

interface TimelineEntry {
  type: string;
  title: string;
  detail: string;
}

interface BlueprintDecisionTimelineProps {
  entries: TimelineEntry[];
}

export default function BlueprintDecisionTimeline({ entries }: BlueprintDecisionTimelineProps) {
  if (entries.length === 0) return null;

  return (
    <details className="shrink-0 border-b border-[var(--border-subtle)] bg-[var(--surface-panel)] px-4 py-2 md:px-5">
      <summary className="cursor-pointer text-[10px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
        Decision timeline ({entries.length})
      </summary>
      <ol className="mt-2 space-y-2 pb-1">
        {entries.map((entry, i) => (
          <li key={`${entry.type}-${i}`} className="flex gap-2 text-xs">
            <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--accent)]" />
            <div>
              <p className="font-medium text-[var(--foreground)]">{entry.title}</p>
              <p className="text-[var(--text-muted)]">{entry.detail}</p>
            </div>
          </li>
        ))}
      </ol>
    </details>
  );
}
