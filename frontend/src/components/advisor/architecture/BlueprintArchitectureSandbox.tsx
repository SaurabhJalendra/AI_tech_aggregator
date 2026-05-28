'use client';

import type { ArchitectureConsultingPayload } from '@/types/chat';
import { useChatStore } from '@/stores/chatStore';

interface BlueprintArchitectureSandboxProps {
  sandbox: ArchitectureConsultingPayload['architecture_sandbox'];
  disabled?: boolean;
}

export default function BlueprintArchitectureSandbox({
  sandbox,
  disabled,
}: BlueprintArchitectureSandboxProps) {
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isStreaming = useChatStore((s) => s.isStreaming);

  if (!sandbox?.postures?.length) return null;

  return (
    <details className="shrink-0 border-b border-[var(--border-subtle)] px-4 py-2 md:px-5">
      <summary className="cursor-pointer text-[10px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
        Architecture sandbox
      </summary>
      <p className="mt-1 text-[11px] text-[var(--text-muted)]">
        Test deployment and scale postures — not manual graph editing.
      </p>
      <div className="mt-2 flex flex-wrap gap-1.5 pb-1">
        {sandbox.postures.map((p) => (
          <button
            key={p.id}
            type="button"
            disabled={disabled || isStreaming}
            onClick={() =>
              sendMessage(`Apply architecture posture: ${p.label}`, {
                current_panel: 'interactive_architecture',
                sandbox_posture: p.id,
              })
            }
            className={`rounded-full border px-2.5 py-1 text-[11px] font-medium disabled:opacity-50 ${
              sandbox.active_posture === p.id
                ? 'border-[var(--accent)]/50 bg-[var(--accent-muted)]/35 text-[var(--foreground)]'
                : 'border-[var(--border-subtle)] text-[var(--text-secondary)] hover:border-[var(--accent)]/30'
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>
    </details>
  );
}
