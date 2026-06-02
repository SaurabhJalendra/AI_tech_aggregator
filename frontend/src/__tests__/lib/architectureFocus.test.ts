import { describe, expect, it } from 'vitest';
import { getActiveStageId, getFocusNodeIds } from '@/lib/architectureFocus';

describe('architectureFocus', () => {
  it('returns connected path for selected node', () => {
    const edges = [
      { from: 'a', to: 'b' },
      { from: 'b', to: 'c' },
      { from: 'x', to: 'y' },
    ];
    const focus = getFocusNodeIds('b', edges);
    expect(focus).toEqual(new Set(['a', 'b', 'c']));
  });

  it('returns null when nothing selected', () => {
    expect(getFocusNodeIds(null, [])).toBeNull();
  });

  it('resolves active stage from node category', () => {
    expect(
      getActiveStageId({
        id: 'e1',
        label: 'BGE',
        category: 'embeddings',
      })
    ).toBe('embeddings');
  });
});
