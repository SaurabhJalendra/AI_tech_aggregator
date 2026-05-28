'use client';

interface BlueprintProactiveInsightsProps {
  insights: string[];
}

export default function BlueprintProactiveInsights({ insights }: BlueprintProactiveInsightsProps) {
  if (insights.length === 0) return null;

  return (
    <div className="shrink-0 border-b border-[var(--border-subtle)] bg-[var(--surface-secondary)]/40 px-4 py-2.5 md:px-5">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
        Architect guidance
      </p>
      <ul className="mt-1.5 space-y-1">
        {insights.map((line) => (
          <li key={line} className="text-xs leading-relaxed text-[var(--text-secondary)]">
            · {line}
          </li>
        ))}
      </ul>
    </div>
  );
}
