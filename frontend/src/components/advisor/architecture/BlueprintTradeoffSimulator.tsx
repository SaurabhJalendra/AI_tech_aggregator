'use client';

import type { ArchitectureConsultingPayload } from '@/types/chat';
import { useChatStore } from '@/stores/chatStore';

interface BlueprintTradeoffSimulatorProps {
  levers: ArchitectureConsultingPayload['tradeoff_simulator'];
  disabled?: boolean;
}

export default function BlueprintTradeoffSimulator({
  levers,
  disabled,
}: BlueprintTradeoffSimulatorProps) {
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isStreaming = useChatStore((s) => s.isStreaming);

  if (!levers?.length) return null;

  return (
    <details className="shrink-0 border-b border-[var(--border-subtle)] bg-[var(--surface-panel)]/80 px-4 py-2 md:px-5">
      <summary className="cursor-pointer text-[10px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
        Strategic tradeoff exploration
      </summary>
      <p className="mt-1 text-[11px] text-[var(--text-muted)]">
        Explore a priority shift — the blueprint re-scores deterministically.
      </p>
      <div className="mt-2 flex flex-wrap gap-1.5 pb-1">
        {levers.map((lever) => (
          <button
            key={lever.id}
            type="button"
            title={lever.tradeoff}
            disabled={disabled || isStreaming}
            onClick={() =>
              sendMessage(
                `Explore infrastructure tradeoff: ${lever.label}. ${lever.tradeoff}`,
                {
                  current_panel: 'interactive_architecture',
                  tradeoff_lever: lever.id,
                }
              )
            }
            className={`rounded-full border px-2.5 py-1 text-[11px] font-medium transition disabled:opacity-50 ${
              lever.active
                ? 'border-[var(--accent)]/50 bg-[var(--accent-muted)]/40 text-[var(--foreground)]'
                : 'border-[var(--border-subtle)] bg-[var(--surface-secondary)] text-[var(--text-secondary)] hover:border-[var(--accent)]/30'
            }`}
          >
            {lever.label}
          </button>
        ))}
      </div>
    </details>
  );
}
