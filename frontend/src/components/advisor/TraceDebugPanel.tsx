'use client';

import { useState } from 'react';
import EntityChip from '@/components/advisor/EntityChip';
import { useChatStore } from '@/stores/chatStore';

/** Collapsible debug view of the latest deterministic advisor trace (Phase-2). */
export default function TraceDebugPanel() {
  const trace = useChatStore((s) => s.lastAdvisorTrace);
  const explain = useChatStore((s) => s.lastRecommendationExplain);
  const [open, setOpen] = useState(false);

  if (!trace && !explain) {
    return null;
  }

  return (
    <div className="border-t border-[var(--border-subtle)] px-4 py-2">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="text-xs font-medium text-[var(--text-muted)] hover:text-[var(--foreground)]"
      >
        {open ? 'Hide' : 'Show'} advisor trace
      </button>
      {open && (
        <div className="mt-2 space-y-2">
          {Array.isArray(explain?.shortlist) && explain.shortlist.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[10px] font-medium text-[var(--text-muted)]">Shortlist:</span>
              {(explain.shortlist as string[]).map((slug, i) => (
                <EntityChip key={slug} slug={slug} rank={i + 1} className="text-xs px-2 py-0.5" />
              ))}
            </div>
          )}
          <pre className="scrollbar-hidden max-h-48 overflow-auto rounded p-2 text-[10px] leading-tight text-[var(--text-secondary)]" style={{ background: 'var(--surface-secondary)' }}>
            {JSON.stringify({ trace, explain }, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
