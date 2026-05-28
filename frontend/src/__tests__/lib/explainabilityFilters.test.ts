import { describe, expect, it } from 'vitest';
import { filterUserVisibleFilters, isUserVisibleFilterReason } from '@/lib/explainabilityFilters';

describe('explainabilityFilters', () => {
  it('hides comparison layer internal filters', () => {
    expect(
      isUserVisibleFilterReason(
        'comparison_layer=foundation_model (mixed abstraction layer)',
      ),
    ).toBe(false);
  });

  it('keeps constraint-driven filters', () => {
    expect(isUserVisibleFilterReason('budget=low')).toBe(true);
  });

  it('filters lists for the explain drawer', () => {
    const items = [
      { slug: 'openai', reason: 'comparison_layer=foundation_model (mixed abstraction layer)' },
      { slug: 'pinecone', reason: 'budget=low' },
    ];
    expect(filterUserVisibleFilters(items)).toEqual([{ slug: 'pinecone', reason: 'budget=low' }]);
  });
});
