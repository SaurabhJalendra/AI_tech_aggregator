import { describe, expect, it } from 'vitest';
import { parseArchitecturePayload } from '@/lib/architecturePayload';

describe('architecture payload simulation', () => {
  it('parses comparison baseline and simulation flag', () => {
    const parsed = parseArchitecturePayload({
      nodes: [{ id: 'v', label: 'Qdrant', slug: 'qdrant', category: 'vector_databases' }],
      edges: [],
      comparison_baseline: {
        title: 'Before',
        nodes: [{ id: 'v', label: 'Pinecone', slug: 'pinecone', category: 'vector_databases' }],
      },
      architecture_consulting: {
        simulation: {
          scenario_id: 's1',
          label: 'Self-hosted',
          slot_updates: {},
          narrative: 'Simulated.',
        },
      },
    });
    expect(parsed.simulationActive).toBe(true);
    expect(parsed.comparisonBaseline?.nodes).toHaveLength(1);
  });
});
