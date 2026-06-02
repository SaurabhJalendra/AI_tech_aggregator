'use client';

import type { EvolutionHistoryEntry } from '@/types/chat';
import { formatEntityLabel } from '@/lib/entityDisplay';

interface BlueprintEvolutionHistoryProps {
  entries: EvolutionHistoryEntry[];
}

export default function BlueprintEvolutionHistory({ entries }: BlueprintEvolutionHistoryProps) {
  if (entries.length === 0) return null;

  return (
    <details className="shrink-0 border-b border-[var(--border-subtle)] px-4 py-2 md:px-5">
      <summary className="cursor-pointer text-[10px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
        Architecture evolution ({entries.length})
      </summary>
      <ol className="mt-2 max-h-40 space-y-2 overflow-y-auto pb-1">
        {entries.map((entry) => (
          <li
            key={entry.id}
            className="rounded-md border border-[var(--border-subtle)] bg-[var(--surface-panel)]/80 px-3 py-2 text-xs"
          >
            <p className="font-medium text-[var(--foreground)]">{entry.title}</p>
            {entry.summary && (
              <p className="mt-0.5 text-[var(--text-muted)] line-clamp-2">{entry.summary}</p>
            )}
            {entry.selections && Object.keys(entry.selections).length > 0 && (
              <p className="mt-1 text-[10px] text-[var(--text-muted)]">
                {Object.values(entry.selections)
                  .slice(0, 4)
                  .map((s) => formatEntityLabel(s))
                  .join(' · ')}
              </p>
            )}
            {entry.transition_reason && (
              <p className="mt-1 italic text-[var(--text-muted)]">{entry.transition_reason}</p>
            )}
          </li>
        ))}
      </ol>
    </details>
  );
}
