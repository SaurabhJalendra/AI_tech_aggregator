import { describe, expect, it } from 'vitest';
import {
  filterSimpleArchitecture,
  parseArchitecturePayload,
} from '@/lib/architecturePayload';

describe('architecturePayload', () => {
  it('normalizes source/target edges', () => {
    const parsed = parseArchitecturePayload({
      nodes: [{ id: 'a', label: 'A' }, { id: 'b', label: 'B' }],
      edges: [{ source: 'a', target: 'b', label: 'flow' }],
    });
    expect(parsed.edges).toEqual([{ from: 'a', to: 'b', label: 'flow' }]);
  });

  it('filters simple view to pipeline categories', () => {
    const nodes = [
      { id: '1', label: 'Ingest', category: 'data_ingestion' },
      { id: '2', label: 'Embed', category: 'embeddings' },
      { id: '3', label: 'LLM', category: 'llm_layer' },
      { id: '4', label: 'Extra', category: 'fine_tuning' },
      { id: '5', label: 'A', category: 'data_ingestion' },
      { id: '6', label: 'B', category: 'chunking' },
      { id: '7', label: 'C', category: 'retrieval' },
      { id: '8', label: 'D', category: 'vector_databases' },
      { id: '9', label: 'E', category: 'fine_tuning' },
    ];
    const edges = [
      { from: '1', to: '2' },
      { from: '2', to: '3' },
    ];
    const { nodes: kept } = filterSimpleArchitecture(nodes, edges);
    expect(kept.some((n) => n.id === '4')).toBe(false);
    expect(kept.length).toBeGreaterThanOrEqual(3);
  });
});
