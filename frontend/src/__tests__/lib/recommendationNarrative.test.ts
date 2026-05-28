import { describe, expect, it } from 'vitest';
import {
  buildRecommendationNarrative,
  tradeoffWinnerNarrative,
} from '@/lib/recommendationNarrative';
import type { ParsedComparison } from '@/lib/comparisonPanel';

const baseComparison: ParsedComparison = {
  modules: ['qdrant', 'pinecone'],
  dimensions: ['performance', 'cost_efficiency', 'scalability'],
  matrix: {
    qdrant: {
      performance: { value: 8, justification: '' },
      cost_efficiency: { value: 7, justification: '' },
      scalability: { value: 9, justification: '' },
    },
    pinecone: {
      performance: { value: 7, justification: '' },
      cost_efficiency: { value: 5, justification: '' },
      scalability: { value: 8, justification: '' },
    },
  },
  overallRanking: ['qdrant', 'pinecone'],
  shortlist: ['qdrant', 'pinecone'],
  highlights: {},
  recommendation: 'Qdrant fits your workload.',
  pipelineScores: { qdrant: 8.2, pinecone: 6.1 },
  weights: {},
  pipelineRanking: ['qdrant', 'pinecone'],
};

describe('buildRecommendationNarrative', () => {
  it('builds consulting narrative with confidence', () => {
    const n = buildRecommendationNarrative(
      baseComparison,
      {
        slots: {
          deployment_preference: {
            value: 'managed',
            source: 'explicit',
            confidence: 1,
          },
        },
        version: '1',
      },
      null,
      'vector_db_comparison'
    );
    expect(n).not.toBeNull();
    expect(n!.pick).toBe('qdrant');
    expect(n!.constraintLeadIn).toContain('managed');
    expect(n!.whyThis.length).toBeGreaterThan(0);
    expect(n!.confidence.headline.length).toBeGreaterThan(0);
  });

  it('uses playbook-specific framing', () => {
    const rag = buildRecommendationNarrative(baseComparison, null, null, 'rag_pipeline_design');
    expect(rag!.playbookFraming.toLowerCase()).toContain('rag');
  });
});

describe('tradeoffWinnerNarrative', () => {
  it('returns human tradeoff line', () => {
    const line = tradeoffWinnerNarrative(
      baseComparison,
      'qdrant',
      'cost_efficiency',
      'performance'
    );
    expect(line.length).toBeGreaterThan(10);
    expect(line).not.toMatch(/8\.7/);
  });
});
