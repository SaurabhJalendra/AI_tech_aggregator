import { describe, expect, it } from 'vitest';
import { humanizeFilterReason } from '@/lib/consultingExplain';

describe('humanizeFilterReason', () => {
  it('converts budget filter to consulting language', () => {
    const text = humanizeFilterReason(
      'pgvector',
      'budget=low excludes high pricing tier'
    );
    expect(text).toContain('pgvector');
    expect(text.toLowerCase()).toContain('budget');
    expect(text).not.toContain('budget=low');
  });

  it('converts self-hosted deployment filter', () => {
    const text = humanizeFilterReason(
      'pinecone',
      'deployment=self_hosted requires on_prem or hybrid'
    );
    expect(text.toLowerCase()).toContain('self-hosted');
    expect(text.toLowerCase()).toContain('pinecone');
  });
});
