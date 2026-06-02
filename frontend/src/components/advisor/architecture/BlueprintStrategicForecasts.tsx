'use client';

import type { StrategicForecast } from '@/types/chat';

interface BlueprintStrategicForecastsProps {
  forecasts: StrategicForecast[];
}

const HORIZON_LABELS: Record<string, string> = {
  near_term: 'Near term',
  medium_term: 'Medium term',
  long_term: 'Long term',
  strategic: 'Strategic',
};

export default function BlueprintStrategicForecasts({ forecasts }: BlueprintStrategicForecastsProps) {
  if (forecasts.length === 0) return null;

  return (
    <details className="shrink-0 border-b border-[var(--border-subtle)] bg-[var(--surface-secondary)]/30 px-4 py-2 md:px-5">
      <summary className="cursor-pointer text-[10px] font-semibold uppercase tracking-wide text-[var(--text-muted)]">
        Strategic outlook ({forecasts.length})
      </summary>
      <ul className="mt-2 space-y-2.5 pb-1">
        {forecasts.map((f) => (
          <li key={`${f.horizon}-${f.title}`} className="text-xs">
            <p className="font-medium text-[var(--foreground)]">
              {f.title}
              <span className="ml-2 font-normal text-[var(--text-muted)]">
                · {HORIZON_LABELS[f.horizon] ?? f.horizon}
              </span>
            </p>
            <p className="mt-0.5 leading-relaxed text-[var(--text-secondary)]">{f.insight}</p>
          </li>
        ))}
      </ul>
    </details>
  );
}
