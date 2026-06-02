'use client';

import { useChatStore } from '@/stores/chatStore';

const SCENARIOS = [
  {
    id: 'budget_up',
    label: 'If budget increases',
    message:
      'What would change in this architecture if our budget increases significantly? Show affected components and tradeoffs.',
  },
  {
    id: 'self_hosted',
    label: 'If self-hosted',
    message:
      'How would this architecture change if we prioritize self-hosted deployment and data control?',
  },
  {
    id: 'scale_up',
    label: 'If scale doubles',
    message:
      'Which components would need to change if query volume and document count double?',
  },
  {
    id: 'latency',
    label: 'If latency critical',
    message:
      'What architectural tradeoffs apply if end-to-end latency becomes the top priority?',
  },
] as const;

interface BlueprintScenarioStripProps {
  disabled?: boolean;
}

export default function BlueprintScenarioStrip({ disabled }: BlueprintScenarioStripProps) {
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isStreaming = useChatStore((s) => s.isStreaming);

  return (
    <div className="shrink-0 border-b border-[var(--border-subtle)] bg-[var(--surface-panel)] px-4 py-2 md:px-5">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
        Explore scenarios · or ask in chat (“What if latency becomes critical?”)
      </p>
      <div className="mt-1.5 flex flex-wrap gap-1.5">
        {SCENARIOS.map((s) => (
          <button
            key={s.id}
            type="button"
            disabled={disabled || isStreaming}
            onClick={() =>
              sendMessage(s.message, {
                current_panel: 'interactive_architecture',
              })
            }
            className="rounded-full border border-[var(--border-subtle)] bg-[var(--surface-secondary)] px-2.5 py-1 text-[11px] font-medium text-[var(--text-secondary)] transition hover:border-[var(--accent)]/40 hover:text-[var(--foreground)] disabled:opacity-50"
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}
