import { describe, expect, it } from 'vitest';
import {
  buildBlueprintConsultingSummary,
  buildGuidedPipelineSteps,
} from '@/lib/architectureBlueprintNarrative';
import type { ArchNode, ConstraintStatePayload } from '@/types/chat';

describe('architectureBlueprintNarrative', () => {
  it('builds priorities from constraint state', () => {
    const state: ConstraintStatePayload = {
      slots: {
        deployment_preference: { value: 'managed', source: 'explicit', confidence: 1 },
        language: { value: 'python', source: 'explicit', confidence: 1 },
        scale: { value: 'growing_application', source: 'explicit', confidence: 1 },
      },
    };
    const summary = buildBlueprintConsultingSummary({
      constraintState: state,
      explain: null,
      nodes: [{ id: 'v', label: 'Qdrant', category: 'vector_databases' }],
      playbookId: 'rag_pipeline_design',
    });
    expect(summary.priorities.length).toBeGreaterThan(0);
    expect(summary.priorities.some((p) => p.toLowerCase().includes('managed'))).toBe(true);
    expect(summary.confidenceHeadline).toBeTruthy();
    expect(summary.confidenceEvidence).toEqual([]);
    expect(summary.evidenceItems).toEqual([]);
  });

  it('merges backend architecture_consulting when present', () => {
    const summary = buildBlueprintConsultingSummary({
      constraintState: null,
      explain: null,
      nodes: [],
      consulting: {
        comparative_priority_line: 'Prioritizes operational simplicity over maximum customization.',
        confidence: {
          tone: 'high',
          headline: 'High-confidence architecture',
          explanation: 'Trace-backed scoring.',
          evidence: ['4 stages scored'],
        },
        priorities: ['Managed deployment'],
        scale_badge: 'Growing production',
      },
    });
    expect(summary.comparativePriorityLine).toContain('operational simplicity');
    expect(summary.confidenceEvidence).toContain('4 stages scored');
    expect(summary.scaleBadge).toBe('Growing production');
  });

  it('builds guided steps for present stages', () => {
    const nodes: ArchNode[] = [
      { id: 'a', label: 'Loader', category: 'data_ingestion' },
      { id: 'b', label: 'BGE', category: 'embeddings' },
      { id: 'c', label: 'Qdrant', category: 'vector_databases' },
    ];
    const steps = buildGuidedPipelineSteps(nodes, [
      'data_processing',
      'embeddings',
      'storage_retrieval',
    ]);
    expect(steps.length).toBe(3);
    expect(steps[0].order).toBe(1);
    expect(steps[0].narrative.length).toBeGreaterThan(10);
  });
});
