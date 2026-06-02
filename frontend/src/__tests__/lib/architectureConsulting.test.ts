import { describe, expect, it } from 'vitest';
import {
  buildNodeConsultingProfile,
  getConsultingNodeTitle,
  humanizeEdgeLabel,
} from '@/lib/architectureConsulting';
import type { ArchNode } from '@/types/chat';

describe('architectureConsulting', () => {
  it('maps vector database category to consulting language', () => {
    const node: ArchNode = {
      id: 'v1',
      label: 'Pinecone',
      category: 'vector_databases',
      slug: 'pinecone',
    };
    expect(getConsultingNodeTitle(node)).toBe('Semantic retrieval storage');
  });

  it('humanizes technical edge labels', () => {
    expect(humanizeEdgeLabel('embeddings')).toBe('Vectors');
    expect(humanizeEdgeLabel('rerank results')).toBe('Ranked results');
  });

  it('builds consulting profile with stage and tradeoffs', () => {
    const profile = buildNodeConsultingProfile({
      id: 'l1',
      label: 'GPT-4',
      category: 'llm_layer',
      slug: 'gpt4_1',
      description: 'Strong reasoning for complex RAG answers.',
    });
    expect(profile.stageLabel).toBe('Generation layer');
    expect(profile.whySelected).toContain('reasoning');
    expect(profile.tradeoffNote).toBeTruthy();
  });
});
