import type { ArchEdge, ArchNode } from '@/types/chat';

export type NodeImportance = 'primary' | 'standard' | 'supporting';

/** Categories that anchor most RAG / retrieval architectures. */
const PRIMARY_CATEGORIES = new Set([
  'vector_databases',
  'llm_layer',
  'rag_architectures',
  'retrieval',
  'embeddings',
]);

/** Typically secondary tuning or plumbing in a first-pass blueprint. */
const SUPPORTING_CATEGORIES = new Set([
  'caching',
  'workflow_orchestration',
  'search_discovery',
  'security_compliance',
]);

function connectionScore(nodeId: string, edges: ArchEdge[]): number {
  let score = 0;
  for (const e of edges) {
    if (e.from === nodeId) score += 1;
    if (e.to === nodeId) score += 1;
  }
  return score;
}

/**
 * Classify visual weight: primary (core decisions), supporting (enablers), standard.
 */
export function inferNodeImportance(
  node: ArchNode,
  edges: ArchEdge[],
  shortlistSlugs?: string[]
): NodeImportance {
  if (node.slug && shortlistSlugs?.includes(node.slug)) {
    return 'primary';
  }

  if (node.category && PRIMARY_CATEGORIES.has(node.category)) {
    if (node.category === 'vector_databases' || node.category === 'llm_layer') {
      return 'primary';
    }
    if (connectionScore(node.id, edges) >= 1) return 'primary';
    return 'standard';
  }

  if (node.category && SUPPORTING_CATEGORIES.has(node.category)) {
    return 'supporting';
  }

  if (connectionScore(node.id, edges) >= 3) {
    return 'primary';
  }

  if (connectionScore(node.id, edges) <= 1 && node.category === 'chunking') {
    return 'supporting';
  }

  return 'standard';
}

export function importanceScale(importance: NodeImportance): number {
  if (importance === 'primary') return 1.03;
  if (importance === 'supporting') return 0.98;
  return 1;
}
