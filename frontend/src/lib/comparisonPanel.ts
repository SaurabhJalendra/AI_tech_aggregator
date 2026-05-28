import type { ConstraintStatePayload, RecommendationExplainPayload } from '@/types/chat';
import { orderEntitiesForDisplay } from '@/lib/entityDisplay';

export const DIMENSION_LABELS: Record<string, string> = {
  performance: 'Performance',
  scalability: 'Scalability',
  ease_of_use: 'Ease of Use',
  cost_efficiency: 'Cost Efficiency',
  community: 'Community',
  maturity: 'Maturity',
  flexibility: 'Flexibility',
  data_privacy: 'Data Privacy',
};

export type MatrixCell = { value: number; justification?: string };
export type ComparisonMatrix = Record<string, Record<string, MatrixCell | number>>;

export interface ParsedComparison {
  modules: string[];
  dimensions: string[];
  matrix: ComparisonMatrix;
  /** Comparison-engine ranking across catalog dimensions (may differ from pipeline). */
  overallRanking: string[];
  /** Pipeline shortlist order when provided by backend. */
  shortlist: string[];
  highlights: Record<string, string[]>;
  recommendation: string;
  pipelineScores: Record<string, number>;
  weights: Record<string, number>;
  /** Authoritative display order: pipeline shortlist → scores → matrix fallback. */
  pipelineRanking: string[];
}

export interface TradeoffPair {
  id: string;
  leftLabel: string;
  rightLabel: string;
  leftDim: string;
  rightDim: string;
}

export const DEFAULT_TRADEOFF_PAIRS: TradeoffPair[] = [
  {
    id: 'cost-performance',
    leftLabel: 'Cost Efficient',
    rightLabel: 'High Performance',
    leftDim: 'cost_efficiency',
    rightDim: 'performance',
  },
  {
    id: 'simplicity-scale',
    leftLabel: 'Operational Simplicity',
    rightLabel: 'Scalability',
    leftDim: 'ease_of_use',
    rightDim: 'scalability',
  },
];

/** Pipeline breakdown keys mapped to comparison dimension keys. */
const BREAKDOWN_TO_DIMENSION: Record<string, string> = {
  latency: 'performance',
  scalability: 'scalability',
  ease_of_use: 'ease_of_use',
  cost_fit: 'cost_efficiency',
  ops_fit: 'ease_of_use',
  deployment_fit: 'data_privacy',
  sdk_fit: 'flexibility',
};

export function parseComparisonPayload(
  data: Record<string, unknown>
): ParsedComparison | null {
  const comparison = data.comparison as Record<string, unknown> | undefined;
  if (!comparison) return null;

  const modules = (comparison.modules as string[]) || [];
  const overallRanking = (comparison.overall_ranking as string[]) || [];
  const shortlist = (comparison.shortlist as string[]) || [];
  const pipelineScores = (comparison.pipeline_scores as Record<string, number>) || {};

  const base = {
    modules,
    dimensions: (comparison.dimensions as string[]) || [],
    matrix: (comparison.matrix as ComparisonMatrix) || {},
    overallRanking,
    shortlist,
    highlights: (comparison.highlights as Record<string, string[]>) || {},
    recommendation: (comparison.recommendation as string) || '',
    pipelineScores,
    weights: (comparison.weights as Record<string, number>) || {},
  };

  return {
    ...base,
    pipelineRanking: resolvePipelineRanking(base, null),
  };
}

/**
 * Pipeline-first display order (matches advisor trace / explain shortlist).
 * Priority: explain.shortlist → comparison.shortlist → pipeline_scores → matrix ranking.
 */
export function resolvePipelineRanking(
  comparison: Omit<ParsedComparison, 'pipelineRanking'>,
  explain: RecommendationExplainPayload | null | undefined
): string[] {
  if (explain?.shortlist?.length) {
    return orderEntitiesForDisplay(comparison.modules, explain.shortlist);
  }
  if (comparison.shortlist.length > 0) {
    return orderEntitiesForDisplay(comparison.modules, comparison.shortlist);
  }
  const byScore = Object.entries(comparison.pipelineScores)
    .sort(([, a], [, b]) => Number(b) - Number(a))
    .map(([slug]) => slug);
  if (byScore.length > 0) {
    return orderEntitiesForDisplay(comparison.modules, byScore);
  }
  return orderEntitiesForDisplay(comparison.modules, comparison.overallRanking);
}

/** Re-attach pipeline ranking when explain arrives after panel render. */
export function withPipelineRanking(
  comparison: ParsedComparison,
  explain: RecommendationExplainPayload | null | undefined
): ParsedComparison {
  const { pipelineRanking: _prev, ...base } = comparison;
  return {
    ...base,
    pipelineRanking: resolvePipelineRanking(base, explain),
  };
}

export function pipelineTopPick(comparison: ParsedComparison): string | undefined {
  return comparison.pipelineRanking[0];
}

/** Matrix #1 when it differs from the pipeline pick (for optional UI hints). */
export function matrixLeaderDiffersFromPipeline(comparison: ParsedComparison): string | null {
  const matrixTop = comparison.overallRanking[0];
  const pipelineTop = comparison.pipelineRanking[0];
  if (!matrixTop || !pipelineTop || matrixTop === pipelineTop) return null;
  return matrixTop;
}

export function getMatrixScore(
  matrix: ComparisonMatrix,
  slug: string,
  dim: string
): { value: number; justification: string } {
  const cell = matrix[slug]?.[dim];
  if (typeof cell === 'number') {
    return { value: cell, justification: '' };
  }
  if (cell && typeof cell === 'object' && cell.value != null) {
    return {
      value: cell.value,
      justification: cell.justification || '',
    };
  }
  return { value: 5, justification: '' };
}

/** Infer which comparison dimensions matter most for visual emphasis. */
export function deriveEmphasizedDimensions(
  weights: Record<string, number>,
  constraintState: ConstraintStatePayload | null,
  explain: RecommendationExplainPayload | null
): Set<string> {
  const merged: Record<string, number> = { ...weights };

  if (constraintState?.slots) {
    const budget = constraintState.slots.budget?.value;
    if (budget === 'low') merged.cost_efficiency = Math.max(merged.cost_efficiency ?? 1, 2.5);
    const scale = constraintState.slots.scale?.value;
    if (scale === 'growing_application' || scale === 'enterprise') {
      merged.scalability = Math.max(merged.scalability ?? 1, 2.5);
      merged.performance = Math.max(merged.performance ?? 1, 2);
    }
    const deploy = constraintState.slots.deployment_preference?.value;
    if (deploy === 'self_hosted') {
      merged.data_privacy = Math.max(merged.data_privacy ?? 1, 2.4);
    }
    const latency = constraintState.slots.latency_priority?.value;
    if (latency === 'high') merged.performance = Math.max(merged.performance ?? 1, 2.8);
  }

  const breakdowns = explain?.score_breakdowns;
  if (breakdowns) {
    const topSlug = explain.shortlist?.[0];
    const topBreakdown = topSlug ? breakdowns[topSlug] : undefined;
    if (topBreakdown) {
      for (const [key, val] of Object.entries(topBreakdown)) {
        const dim = BREAKDOWN_TO_DIMENSION[key] || key;
        merged[dim] = Math.max(merged[dim] ?? 1, 1 + Number(val) / 10);
      }
    }
  }

  const entries = Object.entries(merged).filter(([, w]) => w > 0);
  if (entries.length === 0) return new Set();

  const maxW = Math.max(...entries.map(([, w]) => w));
  const threshold = maxW * 0.75;
  return new Set(entries.filter(([, w]) => w >= threshold).map(([dim]) => dim));
}

export function matchConfidencePercent(
  pipelineScores: Record<string, number>,
  topSlug: string
): number | null {
  const scores = Object.values(pipelineScores);
  if (scores.length < 2) return null;
  const top = pipelineScores[topSlug];
  if (top == null) return null;
  const sorted = [...scores].sort((a, b) => b - a);
  const second = sorted[1] ?? sorted[0];
  const gap = top - second;
  const spread = Math.max(sorted[0] - sorted[sorted.length - 1], 0.01);
  return Math.min(98, Math.max(52, Math.round(55 + (gap / spread) * 40)));
}

export function inferWeaknesses(
  matrix: ComparisonMatrix,
  slug: string,
  dimensions: string[],
  ranking: string[]
): string[] {
  const weaknesses: string[] = [];
  for (const dim of dimensions) {
    const { value, justification } = getMatrixScore(matrix, slug, dim);
    const peers = ranking
      .filter((s) => s !== slug)
      .map((s) => getMatrixScore(matrix, s, dim).value);
    const peerMax = peers.length ? Math.max(...peers) : value;
    if (value <= 5 && value < peerMax - 1) {
      const label = DIMENSION_LABELS[dim] || dim.replace(/_/g, ' ');
      weaknesses.push(
        justification
          ? `${label}: ${justification}`
          : `Weaker ${label.toLowerCase()} vs alternatives`
      );
    }
  }
  return weaknesses.slice(0, 2);
}

export function tradeoffPosition(
  matrix: ComparisonMatrix,
  slug: string,
  leftDim: string,
  rightDim: string
): number {
  const left = getMatrixScore(matrix, slug, leftDim).value;
  const right = getMatrixScore(matrix, slug, rightDim).value;
  const total = left + right || 1;
  return Math.min(1, Math.max(0, right / total));
}
