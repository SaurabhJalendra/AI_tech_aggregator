'use client';

import ArchitectureCanvas from '@/components/advisor/architecture/ArchitectureCanvas';
import { parseArchitecturePayload } from '@/lib/architecturePayload';

interface ArchitectureDiagramProps {
  data: Record<string, unknown>;
}

/** Static architecture_diagram panel — uses the same interactive canvas. */
export default function ArchitectureDiagram({ data }: ArchitectureDiagramProps) {
  const parsed = parseArchitecturePayload(data);
  if (parsed.nodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <p className="text-[var(--text-muted)]">No architecture data to display</p>
      </div>
    );
  }

  return (
    <div className="flex w-full flex-col">
      <ArchitectureCanvas data={data} immersive />
    </div>
  );
}
