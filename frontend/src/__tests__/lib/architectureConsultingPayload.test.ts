import { describe, expect, it } from 'vitest';
import { resolveNodeDecision } from '@/lib/architectureConsultingPayload';
import type { ArchitectureConsultingPayload, ArchNode } from '@/types/chat';

describe('architectureConsultingPayload', () => {
  it('resolves decision by slug and node id', () => {
    const consulting: ArchitectureConsultingPayload = {
      node_decisions: {
        qdrant: {
          selection_reason: 'Qdrant was selected for semantic retrieval storage.',
          considered: [],
          rejected: [{ slug: 'pinecone', label: 'Pinecone', reason: 'cost preference' }],
          tradeoffs_accepted: [],
          operational_implications: 'ops',
          deployment_implications: 'deploy',
          scaling_implications: 'scale',
          workload_fit: 'fit',
        },
        vector_databases: {
          selection_reason: 'by category id',
          considered: [],
          rejected: [],
          tradeoffs_accepted: [],
          operational_implications: 'ops',
          deployment_implications: 'deploy',
          scaling_implications: 'scale',
          workload_fit: 'fit',
        },
      },
    };
    const node: ArchNode = {
      id: 'vector_databases',
      label: 'Qdrant',
      slug: 'qdrant',
      category: 'vector_databases',
    };
    expect(resolveNodeDecision(consulting, node)?.selection_reason).toContain('Qdrant');
  });
});
