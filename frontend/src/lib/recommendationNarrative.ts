import { formatEntityLabel } from '@/lib/entityDisplay';
import { buildConstraintAcknowledgement } from '@/lib/constraintLabels';
import {
  DIMENSION_LABELS,
  getMatrixScore,
  matchConfidencePercent,
  pipelineTopPick,
  type ParsedComparison,
} from '@/lib/comparisonPanel';
import type { ConstraintStatePayload, RecommendationExplainPayload } from '@/types/chat';

export type ConfidenceTone = 'high' | 'solid' | 'moderate';

export interface ConfidencePresentation {
  percent: number | null;
  tone: ConfidenceTone;
  headline: string;
  subline: string;
}

export interface RecommendationNarrative {
  pick: string;
  pickLabel: string;
  playbookId: string | null;
  playbookFraming: string;
  constraintLeadIn: string | null;
  confidence: ConfidencePresentation;
  headline: string;
  summary: string;
  workloadFit: string | null;
  operationalFit: string | null;
  whyThis: string[];
  tradeoffAccepted: string | null;
  whyNotAlternatives: string | null;
}

const PLAYBOOK_FRAMING: Record<string, string> = {
  vector_db_comparison:
    'For your vector storage decision, the advisor weighed deployment model, operational burden, and scale fit.',
  rag_pipeline_design:
    'For your RAG stack, the advisor sequenced retrieval, reranking, and generation choices as one coherent pipeline.',
  module_code:
    'For implementation guidance, the advisor prioritized developer experience and ecosystem fit for your stack.',
  architecture_review:
    'For this architecture review, the advisor validated how each layer supports reliability and evolution.',
  local_ai_stack:
    'For a local-first AI stack, the advisor favored options you can run with minimal managed dependencies.',
};

const DIMENSION_NARRATIVE: Record<string, (high: boolean) => string> = {
  performance: (high) =>
    high
      ? 'Strong latency and throughput for production retrieval workloads.'
      : 'Adequate performance; you may trade peak speed for other priorities.',
  scalability: (high) =>
    high
      ? 'Well suited when document volume or query load will grow over time.'
      : 'Better for moderate scale unless you plan aggressive growth soon.',
  ease_of_use: (high) =>
    high
      ? 'Lower operational burden — easier for teams to adopt and maintain.'
      : 'Expect more hands-on operations or integration work.',
  cost_efficiency: (high) =>
    high
      ? 'Favorable total cost profile for sustained usage at your scale.'
      : 'Higher cost position — often acceptable when managed ops or features matter more.',
  data_privacy: (high) =>
    high
      ? 'Aligns with data residency and deployment control requirements.'
      : 'Less ideal when strict on-prem or sovereignty constraints apply.',
  maturity: (high) =>
    high
      ? 'Production-ready with a mature ecosystem and operational patterns.'
      : 'Earlier-stage tradeoffs — validate fit for your risk tolerance.',
  flexibility: (high) =>
    high
      ? 'Adaptable across use cases and integration patterns.'
      : 'More opinionated — simpler path, less customization headroom.',
  community: (high) =>
    high
      ? 'Healthy ecosystem, docs, and community support for faster delivery.'
      : 'Smaller ecosystem — factor in internal expertise.',
};

function confidencePresentation(
  comparison: ParsedComparison,
  pick: string
): ConfidencePresentation {
  const percent = matchConfidencePercent(comparison.pipelineScores, pick);
  if (percent == null) {
    return {
      percent: null,
      tone: 'solid',
      headline: 'Solid advisor match',
      subline: 'Ranked first for your stated constraints and workload profile.',
    };
  }
  if (percent >= 82) {
    return {
      percent,
      tone: 'high',
      headline: 'High-confidence recommendation',
      subline: 'Clear separation from alternatives on the dimensions that matter most to you.',
    };
  }
  if (percent >= 68) {
    return {
      percent,
      tone: 'solid',
      headline: 'Confident recommendation',
      subline: 'Leads the shortlist with meaningful but not overwhelming separation.',
    };
  }
  return {
    percent,
    tone: 'moderate',
    headline: 'Leading option with tradeoffs',
    subline: 'Best overall fit today — review alternatives if one constraint dominates.',
  };
}

function narrativeForDimension(dim: string, value: number): string {
  const fn = DIMENSION_NARRATIVE[dim];
  if (fn) return fn(value >= 7);
  const label = DIMENSION_LABELS[dim] || dim.replace(/_/g, ' ');
  return value >= 7
    ? `Strong ${label.toLowerCase()} relative to peers.`
    : `Moderate ${label.toLowerCase()} — factor into your priorities.`;
}

function topDimensionNarratives(
  comparison: ParsedComparison,
  pick: string,
  limit = 3
): string[] {
  const scored = comparison.dimensions
    .map((dim) => ({
      dim,
      value: getMatrixScore(comparison.matrix, pick, dim).value,
      justification: getMatrixScore(comparison.matrix, pick, dim).justification,
    }))
    .sort((a, b) => b.value - a.value);

  return scored.slice(0, limit).map(({ dim, value, justification }) => {
    if (justification && justification.length < 120 && !/^\d/.test(justification)) {
      return justification;
    }
    return narrativeForDimension(dim, value);
  });
}

function workloadFitLine(
  constraintState: ConstraintStatePayload | null,
  pick: string
): string | null {
  const scale = constraintState?.slots.scale?.value;
  if (scale === 'enterprise' || scale === 'growing_application') {
    return `${formatEntityLabel(pick)} fits growing or enterprise-scale retrieval and indexing patterns.`;
  }
  if (scale === 'prototype' || scale === 'small') {
    return `${formatEntityLabel(pick)} is appropriate for early-stage workloads while leaving room to scale later.`;
  }
  return `${formatEntityLabel(pick)} matches a typical production AI workload profile.`;
}

function operationalFitLine(
  constraintState: ConstraintStatePayload | null,
  pick: string
): string | null {
  const deploy = constraintState?.slots.deployment_preference?.value;
  if (deploy === 'managed' || deploy === 'cloud') {
    return 'Favors managed operations so your team can focus on product logic, not cluster care.';
  }
  if (deploy === 'self_hosted' || deploy === 'on_prem') {
    return 'Supports self-hosted or hybrid deployment where you control infrastructure.';
  }
  const budget = constraintState?.slots.budget?.value ?? constraintState?.slots.budget_tier?.value;
  if (budget === 'low') {
    return 'Balances capability with lean operational and licensing overhead.';
  }
  return 'Operational profile aligns with teams that want predictable day-two burden.';
}

function whyNotAlternativesLine(
  comparison: ParsedComparison,
  pick: string
): string | null {
  const alts = comparison.pipelineRanking.filter((s) => s !== pick).slice(0, 2);
  if (alts.length === 0) return null;
  const names = alts.map((s) => formatEntityLabel(s)).join(' and ');
  return `Alternatives such as ${names} remain viable but rank lower once your constraints are applied.`;
}

export function buildRecommendationNarrative(
  comparison: ParsedComparison,
  constraintState: ConstraintStatePayload | null,
  explain: RecommendationExplainPayload | null,
  playbookId?: string | null
): RecommendationNarrative | null {
  const pick = pipelineTopPick(comparison);
  if (!pick) return null;

  const pickLabel = formatEntityLabel(pick);
  const pb =
    playbookId ??
    constraintState?.playbook_id ??
    explain?.playbook_id ??
    null;

  const framing =
    (pb && PLAYBOOK_FRAMING[pb]) ||
    'The advisor evaluated options against your requirements and pipeline scoring.';

  const rawRec = comparison.recommendation.replace(/\*\*/g, '').trim();
  const whyThis = topDimensionNarratives(comparison, pick);
  const weaknesses = comparison.pipelineRanking
    .filter((s) => s !== pick)
    .slice(0, 1);

  let tradeoffAccepted: string | null = null;
  const weakDims = comparison.dimensions
    .map((d) => ({ d, v: getMatrixScore(comparison.matrix, pick, d).value }))
    .filter(({ v }) => v <= 5)
    .sort((a, b) => a.v - b.v);
  if (weakDims[0]) {
    tradeoffAccepted = `You are accepting ${DIMENSION_LABELS[weakDims[0].d]?.toLowerCase() || weakDims[0].d.replace(/_/g, ' ')} tradeoffs in exchange for stronger fit elsewhere.`;
  }

  return {
    pick,
    pickLabel,
    playbookId: pb,
    playbookFraming: framing,
    constraintLeadIn: buildConstraintAcknowledgement(constraintState),
    confidence: confidencePresentation(comparison, pick),
    headline: `We recommend ${pickLabel}`,
    summary: rawRec || `${pickLabel} is the strongest match for your current constraints and workload.`,
    workloadFit: workloadFitLine(constraintState, pick),
    operationalFit: operationalFitLine(constraintState, pick),
    whyThis,
    tradeoffAccepted,
    whyNotAlternatives: whyNotAlternativesLine(comparison, pick),
  };
}

/** Human label for tradeoff spectrum winner on a dimension pair. */
export function tradeoffWinnerNarrative(
  comparison: ParsedComparison,
  slug: string,
  leftDim: string,
  rightDim: string
): string {
  const left = getMatrixScore(comparison.matrix, slug, leftDim).value;
  const right = getMatrixScore(comparison.matrix, slug, rightDim).value;
  if (left >= right + 1.5) {
    if (leftDim === 'cost_efficiency') return 'Lowest operational cost profile in this set.';
    if (leftDim === 'ease_of_use') return 'Easiest to deploy and operate day to day.';
    return `Stronger on ${DIMENSION_LABELS[leftDim] || leftDim}.`;
  }
  if (right >= left + 1.5) {
    if (rightDim === 'performance') return 'Best performance headroom in this set.';
    if (rightDim === 'scalability') return 'Best suited for scale-out growth.';
    return `Stronger on ${DIMENSION_LABELS[rightDim] || rightDim}.`;
  }
  return 'Balanced tradeoff between competing goals.';
}
