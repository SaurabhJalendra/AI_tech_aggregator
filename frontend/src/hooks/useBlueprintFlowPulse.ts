'use client';

import { useEffect, useState } from 'react';

/** Cycles active pipeline stage for subtle flow emphasis when idle. */
export function useBlueprintFlowPulse(
  stageIds: string[],
  paused: boolean
): string | null {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (paused || stageIds.length === 0) return undefined;

    const prefersReduced =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) return undefined;

    const id = window.setInterval(() => {
      setIndex((i) => (i + 1) % stageIds.length);
    }, 4200);
    return () => window.clearInterval(id);
  }, [paused, stageIds.length, stageIds.join(',')]);

  if (paused || stageIds.length === 0) return null;
  return stageIds[index] ?? null;
}
