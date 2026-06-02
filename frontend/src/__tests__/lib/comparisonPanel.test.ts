import { describe, expect, it } from 'vitest';
import {
  deriveEmphasizedDimensions,
  getMatrixScore,
  matchConfidencePercent,
  parseComparisonPayload,
  resolvePipelineRanking,
  tradeoffPosition,
} from '@/lib/comparisonPanel';

describe('comparisonPanel', () => {
  const sampleData = {
    comparison: {
      modules: ['qdrant', 'weaviate'],
      overall_ranking: ['qdrant', 'weaviate'],
      dimensions: ['performance', 'cost_efficiency'],
      matrix: {
        qdrant: {
          performance: { value: 8, justification: 'Fast' },
          cost_efficiency: { value: 7, justification: 'Fair cost' },
        },
        weaviate: {
          performance: { value: 6, justification: 'Moderate' },
          cost_efficiency: { value: 9, justification: 'Open source' },
        },
      },
      highlights: { qdrant: ['Strong in performance'] },
      recommendation: 'Pick qdrant',
      pipeline_scores: { qdrant: 8.2, weaviate: 7.1 },
      weights: { cost_efficiency: 2.5, performance: 1.0 },
    },
  };

  it('parses comparison payload', () => {
    const parsed = parseComparisonPayload(sampleData);
    expect(parsed?.overallRanking).toEqual(['qdrant', 'weaviate']);
    expect(parsed?.weights.cost_efficiency).toBe(2.5);
  });

  it('reads matrix scores with justification', () => {
    const parsed = parseComparisonPayload(sampleData)!;
    expect(getMatrixScore(parsed.matrix, 'qdrant', 'performance').value).toBe(8);
    expect(getMatrixScore(parsed.matrix, 'qdrant', 'performance').justification).toBe('Fast');
  });

  it('emphasizes high-weight dimensions', () => {
    const parsed = parseComparisonPayload(sampleData)!;
    const emphasized = deriveEmphasizedDimensions(parsed.weights, null, null);
    expect(emphasized.has('cost_efficiency')).toBe(true);
  });

  it('computes match confidence from pipeline scores', () => {
    expect(matchConfidencePercent({ qdrant: 8.2, weaviate: 7.1 }, 'qdrant')).toBeGreaterThan(50);
  });

  it('positions entities on tradeoff spectrum', () => {
    const parsed = parseComparisonPayload(sampleData)!;
    const q = tradeoffPosition(parsed.matrix, 'qdrant', 'cost_efficiency', 'performance');
    const w = tradeoffPosition(parsed.matrix, 'weaviate', 'cost_efficiency', 'performance');
    expect(q).toBeGreaterThan(w);
  });

  it('prefers pipeline shortlist over comparison matrix ranking for display', () => {
    const data = {
      comparison: {
        modules: ['qdrant', 'pinecone'],
        overall_ranking: ['qdrant', 'pinecone'],
        shortlist: ['pinecone', 'qdrant'],
        dimensions: ['performance'],
        matrix: {
          qdrant: { performance: { value: 9 } },
          pinecone: { performance: { value: 7 } },
        },
        highlights: {},
        recommendation: 'pinecone leads',
        pipeline_scores: { pinecone: 8.33, qdrant: 7.85 },
        weights: {},
      },
    };
    const parsed = parseComparisonPayload(data)!;
    expect(parsed.pipelineRanking[0]).toBe('pinecone');
    expect(resolvePipelineRanking(parsed, { shortlist: ['pinecone', 'qdrant'] })[0]).toBe(
      'pinecone'
    );
  });
});
