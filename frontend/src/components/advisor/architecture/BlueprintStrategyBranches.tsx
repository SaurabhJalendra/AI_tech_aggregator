'use client';

import type { StrategyBranch } from '@/types/chat';
import { useChatStore } from '@/stores/chatStore';
import { usePanelStore } from '@/stores/panelStore';

interface BlueprintStrategyBranchesProps {
  branches: StrategyBranch[];
  disabled?: boolean;
}

export default function BlueprintStrategyBranches({
  branches,
  disabled,
}: BlueprintStrategyBranchesProps) {
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const panelData = usePanelStore((s) => s.panelData);
  const constraintState = useChatStore((s) => s.constraintState);
  const activePlaybookId = useChatStore((s) => s.activePlaybookId);

  if (branches.length === 0) return null;

  return (
    <div className="shrink-0 border-b border-[var(--border-subtle)] bg-[var(--surface-panel)] px-4 py-2.5 md:px-5">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
        Explore strategy branches
      </p>
      <p className="mt-0.5 text-[11px] text-[var(--text-muted)]">
        Each branch shifts operational posture — ask how it would reshape your blueprint.
      </p>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {branches.map((branch) => (
          <button
            key={branch.id}
            type="button"
            disabled={disabled || isStreaming}
            title={`${branch.summary} ${branch.operational_consequence}`}
            onClick={() =>
              sendMessage(
                `Explore the ${branch.label} infrastructure strategy for this architecture. ` +
                  `Explain operational consequences and future tradeoffs.`,
                {
                  current_panel: 'interactive_architecture',
                  current_panel_data: panelData,
                  constraint_state: constraintState ?? undefined,
                  active_playbook_id: activePlaybookId ?? undefined,
                  strategy_branch_id: branch.id,
                }
              )
            }
            className="rounded-full border border-[var(--border-subtle)] bg-[var(--surface-secondary)] px-2.5 py-1 text-[11px] font-medium text-[var(--text-secondary)] transition hover:border-[var(--accent)]/40 hover:text-[var(--foreground)] disabled:opacity-50"
          >
            {branch.label}
          </button>
        ))}
      </div>
    </div>
  );
}
