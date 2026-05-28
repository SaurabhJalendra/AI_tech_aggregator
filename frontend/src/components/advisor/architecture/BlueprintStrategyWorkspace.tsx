'use client';

import { useMemo, useState } from 'react';
import type { ArchitectureConsultingPayload, PinnedStrategy } from '@/types/chat';
import { useChatStore } from '@/stores/chatStore';
import { formatEntityLabel } from '@/lib/entityDisplay';

interface BlueprintStrategyWorkspaceProps {
  consulting: ArchitectureConsultingPayload | null;
  currentTitle: string;
  disabled?: boolean;
}

export default function BlueprintStrategyWorkspace({
  consulting,
  currentTitle,
  disabled,
}: BlueprintStrategyWorkspaceProps) {
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const [selected, setSelected] = useState<string[]>([]);

  const profile = useChatStore((s) => s.consultingProfile);

  const pinned = useMemo(() => {
    const fromConsulting = consulting?.strategy_workspace?.pinned;
    if (fromConsulting?.length) return fromConsulting as PinnedStrategy[];
    const fromProfile = (profile?.strategy_workspace as { pinned?: PinnedStrategy[] } | undefined)
      ?.pinned;
    return fromProfile ?? [];
  }, [consulting?.strategy_workspace?.pinned, profile]);

  const multi = consulting?.multi_strategy_overview;

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 2) return [prev[1], id];
      return [...prev, id];
    });
  };

  return (
    <div className="shrink-0 border-b border-[var(--border-subtle)] bg-[var(--surface-panel)] px-4 py-3 md:px-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--accent)]">
            Strategy workspace
          </p>
          <p className="mt-0.5 text-[11px] text-[var(--text-muted)]">
            Pin architecture futures · compare competing deployment paths
          </p>
        </div>
        <button
          type="button"
          disabled={disabled || isStreaming}
          onClick={() =>
            sendMessage(`Pin "${currentTitle}" to my strategy workspace`, {
              current_panel: 'interactive_architecture',
              pin_current_strategy: true,
            })
          }
          className="rounded-md border border-[var(--accent)]/40 bg-[var(--accent-muted)]/30 px-2.5 py-1 text-[11px] font-medium text-[var(--accent)] hover:bg-[var(--accent-muted)]/50 disabled:opacity-50"
        >
          Pin current
        </button>
      </div>

      {multi && multi.strategies.length > 0 && (
        <div className="mt-3 space-y-2">
          <p className="text-xs font-medium text-[var(--foreground)]">{multi.theme}</p>
          {multi.consulting_summary && (
            <p className="text-[11px] text-[var(--text-muted)]">{multi.consulting_summary}</p>
          )}
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {multi.strategies.map((s) => (
              <div
                key={s.pin_id ?? s.title}
                className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-secondary)] p-2.5 text-xs"
              >
                <p className="font-semibold text-[var(--foreground)]">{s.title}</p>
                <p className="mt-1 text-[var(--text-secondary)] line-clamp-2">
                  {s.comparative_priority_line}
                </p>
                {s.cost_evolution?.trajectories?.[0] && (
                  <p className="mt-2 text-[10px] italic text-[var(--text-muted)]">
                    {s.cost_evolution.trajectories[0].insight}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {pinned.length > 0 && !multi && (
        <div className="mt-3">
          <ul className="space-y-1.5">
            {pinned.map((p) => (
              <li key={p.id} className="flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={selected.includes(p.id)}
                  onChange={() => toggleSelect(p.id)}
                  className="rounded border-[var(--border-subtle)]"
                />
                <span className="font-medium text-[var(--foreground)]">{p.title}</span>
                <span className="text-[var(--text-muted)]">
                  {p.selections &&
                    Object.values(p.selections)
                      .slice(0, 3)
                      .map((s) => formatEntityLabel(s))
                      .join(' · ')}
                </span>
              </li>
            ))}
          </ul>
          <button
            type="button"
            disabled={disabled || isStreaming || selected.length < 2}
            onClick={() =>
              sendMessage('Compare my pinned architecture strategies side by side', {
                current_panel: 'interactive_architecture',
                compare_pin_ids: selected,
              })
            }
            className="mt-2 rounded-md border border-[var(--border-subtle)] px-2.5 py-1 text-[11px] font-medium text-[var(--text-secondary)] hover:border-[var(--accent)]/40 disabled:opacity-40"
          >
            Compare selected ({selected.length}/2)
          </button>
        </div>
      )}
    </div>
  );
}
