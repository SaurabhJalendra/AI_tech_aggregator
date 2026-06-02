import { describe, expect, it } from 'vitest';
import { inferNodeImportance } from '@/lib/architectureNodeHierarchy';
import type { ArchEdge, ArchNode } from '@/types/chat';

describe('architectureNodeHierarchy', () => {
  it('marks vector store and LLM as primary', () => {
    const edges: ArchEdge[] = [
      { from: 'e', to: 'v' },
      { from: 'v', to: 'l' },
    ];
    expect(
      inferNodeImportance(
        { id: 'v', label: 'Qdrant', category: 'vector_databases' },
        edges
      )
    ).toBe('primary');
    expect(
      inferNodeImportance({ id: 'l', label: 'GPT', category: 'llm_layer' }, edges)
    ).toBe('primary');
  });

  it('marks shortlist slugs as primary', () => {
    expect(
      inferNodeImportance(
        { id: 'c', label: 'Cache', category: 'caching', slug: 'redis' },
        [],
        ['redis']
      )
    ).toBe('primary');
  });
});
