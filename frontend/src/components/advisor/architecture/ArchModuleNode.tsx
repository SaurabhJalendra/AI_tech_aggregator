'use client';

import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { getArchCategoryStyle } from '@/lib/architectureColors';
import { importanceScale } from '@/lib/architectureNodeHierarchy';
import type { ArchFlowNodeData } from '@/lib/architectureLayout';
import { ARCH_NODE_HEIGHT, ARCH_NODE_WIDTH } from '@/lib/architectureLayout';

function ArchModuleNodeComponent({ data, selected }: NodeProps) {
  const d = data as ArchFlowNodeData;
  const style = getArchCategoryStyle(d.category);
  const isActive = d.selected || d.highlighted || selected;
  const importance = d.importance ?? 'standard';
  const opacity = d.dimmed ? 0.3 : importance === 'supporting' ? 0.72 : 1;
  const scale = isActive ? 1.02 : importanceScale(importance);
  const evolved = d.evolved;
  const fitClass =
    d.fitStrength === 'strong'
      ? 'arch-fit-strong'
      : d.fitStrength === 'moderate'
        ? 'arch-fit-moderate'
        : '';

  return (
    <div
      className={`arch-module-node ${evolved ? 'arch-node-evolved' : ''} ${d.flowActive ? 'arch-node-flow-active' : ''} ${fitClass}`}
      style={{
        width: ARCH_NODE_WIDTH,
        height: ARCH_NODE_HEIGHT,
        opacity,
        transform: `scale(${scale})`,
        transition: 'opacity 0.32s ease, transform 0.28s ease',
      }}
    >
      <Handle type="target" position={Position.Left} className="!h-2 !w-2 !border-0 !bg-transparent" />
      <Handle type="source" position={Position.Right} className="!h-2 !w-2 !border-0 !bg-transparent" />

      <div
        className={`flex h-full flex-col rounded-xl border px-4 py-3 ${
          importance === 'primary'
            ? 'shadow-[0_6px_20px_rgba(15,23,42,0.08)]'
            : 'shadow-[var(--shadow-soft)]'
        }`}
        style={{
          backgroundColor: style.fill,
          borderColor: isActive ? 'var(--accent)' : style.stroke,
          borderWidth: isActive ? 2 : importance === 'primary' ? 1.5 : 1,
          boxShadow: isActive
            ? '0 0 0 3px var(--accent-muted), var(--shadow-soft)'
            : undefined,
        }}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex min-w-0 flex-1 items-start gap-2">
            <span
              className="mt-1 h-2 w-2 shrink-0 rounded-full"
              style={{ backgroundColor: style.accent }}
              aria-hidden
            />
            <div className="min-w-0">
              <p
                className="truncate text-[10px] font-medium uppercase tracking-wide"
                style={{ color: style.text, opacity: 0.72 }}
              >
                {d.stageLabel ?? 'Component'}
              </p>
              <p
                className={`mt-0.5 truncate font-semibold leading-snug ${
                  importance === 'primary' ? 'text-[16px]' : 'text-[15px]'
                }`}
                style={{ color: style.text }}
                title={d.consultingTitle || d.label}
              >
                {d.consultingTitle || d.label}
              </p>
            </div>
          </div>
          {importance === 'primary' && (
            <span className="shrink-0 rounded-md bg-[var(--accent-muted)] px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-[var(--accent)]">
              Core
            </span>
          )}
          {importance === 'supporting' && (
            <span className="shrink-0 rounded-md border border-[var(--border-subtle)] px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide text-[var(--text-muted)]">
              Support
            </span>
          )}
        </div>
        <p
          className="mt-2 line-clamp-2 text-[12px] leading-snug"
          style={{ color: style.text, opacity: 0.8 }}
          title={d.roleLine}
        >
          {d.roleLine}
        </p>
        {d.label !== d.consultingTitle && d.consultingTitle ? (
          <p className="mt-1 truncate text-[10px] text-[var(--text-muted)]" title={d.label}>
            {d.label}
          </p>
        ) : null}
      </div>
    </div>
  );
}

export default memo(ArchModuleNodeComponent);
