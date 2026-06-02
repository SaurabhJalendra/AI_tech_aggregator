import { getStageIdForCategory } from '@/lib/architectureStages';
import type { ArchEdge, ArchNode } from '@/types/chat';

export function getActiveStageId(node: ArchNode | null): string | null {
  if (!node) return null;
  return getStageIdForCategory(node.category, node.slug);
}

/** Nodes on paths connected to the selected node (upstream + downstream). */
export function getFocusNodeIds(  selectedId: string | null,
  edges: ArchEdge[]
): Set<string> | null {
  if (!selectedId) return null;

  const upstream = new Set<string>([selectedId]);
  const downstream = new Set<string>([selectedId]);
  let changed = true;

  while (changed) {
    changed = false;
    for (const e of edges) {
      if (downstream.has(e.from) && !downstream.has(e.to)) {
        downstream.add(e.to);
        changed = true;
      }
      if (upstream.has(e.to) && !upstream.has(e.from)) {
        upstream.add(e.from);
        changed = true;
      }
    }
  }

  return new Set([...upstream, ...downstream]);
}
