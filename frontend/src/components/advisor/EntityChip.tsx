'use client';

import { useMemo } from 'react';
import { formatEntityLabel } from '@/lib/entityColors';
import { normalizeEntityKey } from '@/lib/entityDisplay';
import { getEntityChipStyleFromColor, getSessionEntityColor } from '@/lib/visualIdentity';
import { useVisualIdentityStore } from '@/stores/visualIdentityStore';

interface EntityChipProps {
  slug: string;
  rank?: number;
  className?: string;
}

/** Ranking chip / shortlist tag with session-stable entity color. */
export default function EntityChip({ slug, rank, className = '' }: EntityChipProps) {
  const key = normalizeEntityKey(slug);

  // Subscribe to a stable primitive — never return a new object from the selector.
  const color = useVisualIdentityStore((s) => {
    const assigned = s.snapshot.entityColors[key];
    if (assigned) return assigned;
    return getSessionEntityColor(s.snapshot, slug);
  });

  const style = useMemo(() => getEntityChipStyleFromColor(color), [color]);

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-3 py-1 text-sm font-medium ${className}`}
      style={style}
      data-entity={slug}
    >
      {rank != null ? `#${rank} ` : null}
      {formatEntityLabel(slug)}
    </span>
  );
}
