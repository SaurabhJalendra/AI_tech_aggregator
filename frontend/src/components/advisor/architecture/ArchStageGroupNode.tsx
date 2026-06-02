'use client';

import { memo } from 'react';
import type { NodeProps } from '@xyflow/react';
import { getStageFlowDescription } from '@/lib/architectureConsulting';
import type { StageGroupData } from '@/lib/architectureLayout';

function ArchStageGroupNodeComponent({ data }: NodeProps) {
  const d = data as StageGroupData;
  const flowHint = getStageFlowDescription(d.stageId);

  return (
    <div
      className="pointer-events-none rounded-2xl border transition-all duration-300"
      style={{
        width: d.width,
        height: d.height,
        borderColor: d.active || d.flowActive ? 'var(--accent)' : 'var(--border-subtle)',
        borderWidth: d.active ? 2 : 1,
        backgroundColor: d.active
          ? 'color-mix(in srgb, var(--accent-muted) 28%, var(--surface-secondary))'
          : 'var(--surface-secondary)',
        opacity: d.dimmed ? 0.45 : d.flowActive ? 1 : 0.92,
        boxShadow: d.active
          ? 'inset 0 1px 0 rgba(255,255,255,0.06), 0 0 0 1px var(--accent-muted)'
          : 'inset 0 1px 0 rgba(255,255,255,0.04)',
      }}
    >
      <div className="px-5 pt-4">
        <p
          className={`text-[11px] font-semibold uppercase tracking-[0.14em] ${
            d.active ? 'text-[var(--accent)]' : 'text-[var(--text-muted)]'
          }`}
        >
          {d.label}
        </p>
        <p className="mt-1 max-w-[220px] text-[11px] leading-snug text-[var(--text-muted)]">
          {flowHint}
        </p>
      </div>
    </div>
  );
}

export default memo(ArchStageGroupNodeComponent);
