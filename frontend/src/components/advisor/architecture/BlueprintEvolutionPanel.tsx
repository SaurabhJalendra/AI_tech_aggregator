'use client';

import type { ArchitectureEvolution } from '@/types/chat';

interface BlueprintEvolutionPanelProps {
  evolution: ArchitectureEvolution;
  adaptationMessage?: string | null;
  onDismiss?: () => void;
}

export default function BlueprintEvolutionPanel({
  evolution,
  adaptationMessage,
  onDismiss,
}: BlueprintEvolutionPanelProps) {
  return (
    <div
      className="blueprint-evolution-panel shrink-0 border-b border-[var(--accent)]/25 bg-[var(--accent-muted)]/25 px-4 py-3 md:px-5"
      role="status"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-[var(--accent)]">
            Architecture evolved
          </p>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">
            {adaptationMessage || evolution.summary}
          </p>
          {evolution.replacements.length > 0 && (
            <ul className="mt-3 space-y-2">
              {evolution.replacements.map((r) => (
                <li
                  key={`${r.stage}-${r.to_slug}`}
                  className="flex flex-wrap items-center gap-2 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-panel)]/90 px-3 py-2 text-xs"
                >
                  <span className="font-medium text-[var(--text-muted)]">{r.stage_label}</span>
                  <span className="text-[var(--text-muted)]">·</span>
                  <span className="line-through opacity-60">{r.from_label}</span>
                  <span className="text-[var(--accent)]" aria-hidden>
                    →
                  </span>
                  <span className="font-semibold text-[var(--foreground)]">{r.to_label}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="shrink-0 rounded-md px-2 py-1 text-xs text-[var(--text-muted)] hover:bg-[var(--surface-hover)]"
          >
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
}
