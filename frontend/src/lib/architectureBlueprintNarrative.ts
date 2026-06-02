import { buildConstraintAcknowledgement } from '@/lib/constraintLabels';
import { formatEntityLabel } from '@/lib/entityDisplay';
import { getStageIdForCategory, getStageLabel, orderedStageIds } from '@/lib/architectureStages';
import type {
  ArchitectureConsultingPayload,
  ArchEdge,
  ArchNode,
  ConstraintStatePayload,
  RecommendationExplainPayload,
} from '@/types/chat';

export type BlueprintConfidenceTone = 'high' | 'solid' | 'moderate';

export interface BlueprintConsultingSummary {
  title: string;
  subtitle: string;
  confidenceHeadline: string;
  confidenceSubline: string;
  confidenceTone: BlueprintConfidenceTone;
  confidenceEvidence: string[];
  priorities: string[];
  workloadLabel: string | null;
  scaleBadge: string | null;
  operationalComplexity: string | null;
  comparativePriorityLine: string | null;
  deploymentRationale: string | null;
  scalingRationale: string | null;
  trustLine: string;
  continuityFraming: string | null;
  strongestEvidence: string | null;
  evidenceItems: Array<{ tier: string; label: string; detail: string }>;
}

export interface GuidedPipelineStep {
  stageId: string;
  order: number;
  title: string;
  narrative: string;
}

const PLAYBOOK_SUMMARY: Record<string, string> = {
  rag_pipeline_design:
    'A constraint-aware RAG pipeline sequenced for retrieval quality, generation reliability, and day-two operations.',
  architecture_review:
    'An architecture shaped for reliability, evolution, and alignment with how your team actually ships AI features.',
  local_ai_stack:
    'A local-first stack that keeps sensitive workloads under your control while staying practical to run.',
};

const STAGE_GUIDED_NARRATIVE: Record<string, string> = {
  data_processing:
    'Source documents enter here — ingestion and preprocessing prepare content for search.',
  embeddings:
    'Text becomes vector representations so semantic similarity search can run at scale.',
  storage_retrieval:
    'Queries retrieve the most relevant context from your vector store and search layer.',
  ranking:
    'Retrieved candidates are re-ordered so the generator sees the highest-signal context first.',
  rag_generation:
    'The language model composes answers grounded in retrieved evidence.',
  quality_ops:
    'Evaluation and deployment patterns keep quality visible as the system evolves.',
  other: 'Supporting services that keep the pipeline dependable in production.',
};

function workloadLabelFromConstraints(state: ConstraintStatePayload | null): string | null {
  if (!state?.slots) return null;
  const scale = state.slots.scale?.value;
  const useCase = state.slots.use_case?.value;
  const parts: string[] = [];

  if (scale === 'enterprise') parts.push('enterprise-scale production');
  else if (scale === 'growing_application') parts.push('medium-scale production');
  else if (scale === 'prototype' || scale === 'small') parts.push('early production / growth-ready');
  else parts.push('production-oriented');

  if (useCase === 'rag' || useCase === 'RAG') parts.push('RAG workload');
  else if (typeof useCase === 'string') parts.push(`${String(useCase).replace(/_/g, ' ')} workload`);
  else parts.push('AI workload');

  return parts.join(' · ');
}

function derivePriorities(state: ConstraintStatePayload | null): string[] {
  if (!state?.slots) {
    return [
      'Coherent end-to-end pipeline design',
      'Balanced retrieval and generation fit',
      'Reasonable operational complexity',
    ];
  }

  const priorities: string[] = [];
  const deploy =
    state.slots.deployment_preference?.value ?? state.slots.deployment?.value;
  if (deploy === 'managed' || deploy === 'cloud') {
    priorities.push('Managed deployment and operational simplicity');
  } else if (deploy === 'self_hosted' || deploy === 'on_prem') {
    priorities.push('Deployment control and data residency');
  }

  const budget = state.slots.budget?.value ?? state.slots.budget_tier?.value;
  if (budget === 'low') priorities.push('Cost-efficient operations at sustained usage');
  else priorities.push('Production reliability over experimental shortcuts');

  const lang = state.slots.language?.value;
  if (lang === 'python' || lang === 'Python') {
    priorities.push('Fast iteration for Python-heavy teams');
  }

  const scale = state.slots.scale?.value;
  if (scale === 'enterprise' || scale === 'growing_application') {
    priorities.push('Scalable semantic retrieval as volume grows');
  } else {
    priorities.push('Room to grow without re-architecting early choices');
  }

  if (state.slots.prefer_open_source?.value === true) {
    priorities.push('Open-source friendly components where it matters');
  }

  return priorities.slice(0, 4);
}

function confidenceFromExplain(
  explain: RecommendationExplainPayload | null,
  nodeCount: number
): Pick<BlueprintConsultingSummary, 'confidenceHeadline' | 'confidenceSubline' | 'confidenceTone'> {
  const steps = explain?.reasoning_steps?.length ?? 0;
  const filtered = explain?.applied_filters?.length ?? 0;
  const shortlist = explain?.shortlist?.length ?? 0;

  if (shortlist >= 3 && steps >= 2) {
    return {
      confidenceTone: 'high',
      confidenceHeadline: 'High-confidence architecture',
      confidenceSubline:
        'Each layer was scored and filtered against your constraints before placement in this blueprint.',
    };
  }
  if (nodeCount >= 4 || filtered > 0) {
    return {
      confidenceTone: 'solid',
      confidenceHeadline: 'Advisor-engineered blueprint',
      confidenceSubline: 'Components were selected to work together for your stated workload and constraints.',
    };
  }
  return {
    confidenceTone: 'moderate',
    confidenceHeadline: 'Recommended starting architecture',
    confidenceSubline: 'Explore each layer — constraints and alternatives refine as you iterate with the advisor.',
  };
}

export function buildBlueprintConsultingSummary(options: {
  title?: string;
  playbookId?: string | null;
  constraintState: ConstraintStatePayload | null;
  explain: RecommendationExplainPayload | null;
  nodes: ArchNode[];
  consulting?: ArchitectureConsultingPayload | null;
}): BlueprintConsultingSummary {
  const { title, playbookId, constraintState, explain, nodes, consulting } = options;
  const playbookKey =
    consulting?.playbook_id ??
    playbookId ??
    explain?.playbook_id ??
    constraintState?.playbook_id ??
    null;
  const ack = buildConstraintAcknowledgement(constraintState);
  const workloadLabel =
    consulting?.workload_framing ?? workloadLabelFromConstraints(constraintState);
  const priorities =
    consulting?.priorities?.length ? consulting.priorities : derivePriorities(constraintState);
  const fallbackConfidence = confidenceFromExplain(explain, nodes.length);

  const confidence = consulting?.confidence
    ? {
        confidenceTone: consulting.confidence.tone as BlueprintConfidenceTone,
        confidenceHeadline: consulting.confidence.headline,
        confidenceSubline: consulting.confidence.explanation,
        confidenceEvidence:
          consulting.confidence.evidence ??
          consulting.confidence.evidence_hierarchy?.map(
            (e) => `${e.label}: ${e.detail}`
          ) ??
          [],
      }
    : {
        ...fallbackConfidence,
        confidenceEvidence: [] as string[],
      };

  const playbookLine =
    (playbookKey && PLAYBOOK_SUMMARY[playbookKey]) ||
    'An intentional AI infrastructure blueprint aligned with your constraints and workload.';

  const comparativeLine = consulting?.comparative_priority_line ?? null;
  const subtitle = comparativeLine
    ? `${ack ? ack.replace(/,\s*$/, '') : ''}${comparativeLine}`.trim()
    : ack
      ? `${ack.replace(/,\s*$/, '')} this design prioritizes ${priorities[0]?.toLowerCase() ?? 'coherent system fit'}.`
      : playbookLine;

  const coreNames = nodes
    .filter((n) =>
      ['vector_databases', 'llm_layer', 'rag_architectures'].includes(n.category ?? '')
    )
    .map((n) => formatEntityLabel(n.slug ?? n.label))
    .slice(0, 2);

  const trustLine =
    coreNames.length >= 2
      ? `Anchored by ${coreNames[0]} and ${coreNames[1]} — selected over alternatives that scored lower for your constraints.`
      : 'Every component was placed deliberately; select any block to see the decision path.';

  return {
    title: title || 'Recommended architecture',
    subtitle,
    priorities,
    workloadLabel: workloadLabel ?? null,
    scaleBadge: consulting?.scale_badge ?? null,
    operationalComplexity: consulting?.operational_complexity ?? null,
    comparativePriorityLine: comparativeLine,
    deploymentRationale: consulting?.deployment_rationale ?? null,
    scalingRationale: consulting?.scaling_rationale ?? null,
    trustLine,
    continuityFraming: consulting?.continuity_framing ?? null,
    strongestEvidence:
      consulting?.evidence_hierarchy?.strongest ??
      consulting?.confidence?.strongest_evidence ??
      null,
    evidenceItems: consulting?.evidence_hierarchy?.items ?? [],
    ...confidence,
  };
}

export function buildGuidedPipelineSteps(
  nodes: ArchNode[],
  stageIdsPresent: string[]
): GuidedPipelineStep[] {
  const order = orderedStageIds();
  let stepOrder = 0;

  return order
    .filter((stageId) => stageIdsPresent.includes(stageId))
    .map((stageId) => {
      const sample = nodes.find(
        (n) => getStageIdForCategory(n.category, n.slug) === stageId
      );
      stepOrder += 1;
      return {
        stageId,
        order: stepOrder,
        title: getStageLabel(stageId),
        narrative:
          sample?.description && sample.description.length > 20
            ? sample.description
            : STAGE_GUIDED_NARRATIVE[stageId] ?? STAGE_GUIDED_NARRATIVE.other,
      };
    });
}

export function activeGuidedStepIndex(
  steps: GuidedPipelineStep[],
  activeStageId: string | null
): number | null {
  if (!activeStageId) return null;
  const idx = steps.findIndex((s) => s.stageId === activeStageId);
  return idx >= 0 ? idx : null;
}
