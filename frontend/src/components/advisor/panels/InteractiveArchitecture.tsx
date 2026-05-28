'use client';

import { usePanelStore } from '@/stores/panelStore';
import ArchitectureCanvas from '@/components/advisor/architecture/ArchitectureCanvas';
import CodeBlock, { type CodeBlockData } from './CodeBlock';

interface InteractiveArchitectureProps {
  data: Record<string, unknown>;
}

export default function InteractiveArchitecture({ data }: InteractiveArchitectureProps) {
  const codeDrawer = data.codeDrawer as CodeBlockData | undefined;
  const clearCodeDrawer = usePanelStore((s) => s.clearCodeDrawer);

  return (
    <div className="flex w-full flex-col">
      <div className={codeDrawer ? 'flex min-h-0 flex-col' : 'flex w-full flex-col'}>
        <ArchitectureCanvas data={data} showCodeDrawer={Boolean(codeDrawer)} immersive />
      </div>

      {codeDrawer && (
        <div className="flex max-h-[38%] min-h-[200px] shrink-0 flex-col border-t border-[var(--border-subtle)] bg-[var(--surface-secondary)]">
          <div className="flex items-center justify-between border-b border-[var(--border-subtle)] px-4 py-2">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
                Integration code
              </p>
              <p className="text-sm font-semibold text-[var(--foreground)]">
                {codeDrawer.moduleName || codeDrawer.title || 'Selected block'}
              </p>
            </div>
            <button
              type="button"
              onClick={clearCodeDrawer}
              className="rounded-lg px-2 py-1 text-xs text-[var(--text-secondary)] hover:bg-[var(--surface-hover)]"
            >
              Close
            </button>
          </div>
          <div className="scrollbar-hidden min-h-0 flex-1 overflow-y-auto p-4">
            <CodeBlock data={codeDrawer} compact />
          </div>
        </div>
      )}
    </div>
  );
}
