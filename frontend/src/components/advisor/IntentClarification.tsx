'use client';

import { useChatStore } from '@/stores/chatStore';
import { intentLabel } from '@/lib/intentLabels';

export default function IntentClarification() {
  const awaiting = useChatStore((s) => s.awaitingIntentClarification);
  const alternatives = useChatStore((s) => s.intentAlternatives);
  const alternativeLabels = useChatStore((s) => s.intentAlternativeLabels);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const sendClarificationChoice = useChatStore((s) => s.sendClarificationChoice);

  if (!awaiting || alternatives.length === 0) {
    return null;
  }

  const chips = alternatives.map((intentId, index) => {
    const label = alternativeLabels[index] || intentLabel(intentId);
    return (
      <button
        key={intentId}
        type="button"
        disabled={isStreaming}
        onClick={() => sendClarificationChoice(intentId, label)}
        className="rounded-full border border-[var(--border-subtle)] bg-[var(--surface-panel)] px-3 py-1.5 text-xs font-medium text-[var(--foreground)] shadow-[var(--shadow-soft)] transition hover:bg-[var(--surface-hover)] disabled:cursor-not-allowed disabled:opacity-50"
      >
        {label}
      </button>
    );
  });

  return (
    <section
      className="rounded-lg border border-[var(--border-subtle)] p-3"
      style={{ background: 'var(--emphasis-warm)' }}
    >
      <p className="mb-2 text-xs font-medium text-[var(--text-secondary)]">
        Which track should we use?
      </p>
      <section className="flex flex-wrap gap-2">{chips}</section>
    </section>
  );
}
