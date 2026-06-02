'use client';

import { useChatStore } from '@/stores/chatStore';
import { constraintStateToChips } from '@/lib/constraintLabels';

/**
 * Visible consulting memory — active constraints for this conversation.
 */
export default function ConstraintChipBar() {
  const constraintState = useChatStore((s) => s.constraintState);
  const chips = constraintStateToChips(constraintState);

  if (chips.length === 0) {
    return null;
  }

  return (
    <div
      className="border-b border-[var(--border-subtle)] bg-[var(--surface-secondary)] px-4 py-2.5"
      aria-label="Active constraints"
    >
      <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
        Your requirements
      </p>
      <div className="flex flex-wrap gap-1.5">
        {chips.map((chip) => (
          <span
            key={chip.id}
            className="inline-flex items-center rounded-full border border-[var(--border-subtle)] bg-[var(--surface-panel)] px-2.5 py-0.5 text-xs font-medium text-[var(--text-secondary)]"
          >
            {chip.label}
          </span>
        ))}
      </div>
    </div>
  );
}
