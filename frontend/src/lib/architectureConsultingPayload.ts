import type {
  ArchitectureConsultingPayload,
  ArchitectureNodeDecision,
  ArchNode,
} from '@/types/chat';

export function parseArchitectureConsulting(
  data: Record<string, unknown>
): ArchitectureConsultingPayload | null {
  const raw = data.architecture_consulting;
  if (!raw || typeof raw !== 'object') return null;
  return raw as ArchitectureConsultingPayload;
}

/** Resolve pipeline-backed node decision by slug or category node id. */
export function resolveNodeDecision(
  consulting: ArchitectureConsultingPayload | null,
  node: ArchNode
): ArchitectureNodeDecision | null {
  if (!consulting?.node_decisions) return null;
  const decisions = consulting.node_decisions;
  if (node.slug && decisions[node.slug]) return decisions[node.slug];
  if (decisions[node.id]) return decisions[node.id];
  if (node.category && decisions[node.category]) return decisions[node.category];
  return null;
}
