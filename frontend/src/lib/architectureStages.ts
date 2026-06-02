/** Pipeline stage grouping for consulting blueprint layout. */

export interface ArchitectureStage {
  id: string;
  label: string;
  shortLabel: string;
  categories: string[];
  /** Slug substrings that map to this stage when category alone is ambiguous */
  slugHints?: string[];
}

export const ARCHITECTURE_STAGES: ArchitectureStage[] = [
  {
    id: 'data_processing',
    label: 'Data processing',
    shortLabel: 'Intake',
    categories: ['data_ingestion', 'chunking'],
  },
  {
    id: 'embeddings',
    label: 'Embedding layer',
    shortLabel: 'Embed',
    categories: ['embeddings'],
  },
  {
    id: 'storage_retrieval',
    label: 'Retrieval layer',
    shortLabel: 'Retrieve',
    categories: ['vector_databases', 'retrieval', 'caching', 'search_discovery'],
  },
  {
    id: 'ranking',
    label: 'Ranking layer',
    shortLabel: 'Rank',
    categories: [],
    slugHints: ['rerank', 'reranking', 'cross_encoder', 'colbert'],
  },
  {
    id: 'rag_generation',
    label: 'Generation layer',
    shortLabel: 'Generate',
    categories: ['rag_architectures', 'llm_layer', 'agent_systems', 'voice_conversational'],
  },
  {
    id: 'quality_ops',
    label: 'Evaluation & observability',
    shortLabel: 'Evaluate',
    categories: ['evaluation', 'deployment', 'workflow_orchestration', 'security_compliance'],
  },
];

export const SIMPLE_VIEW_CATEGORIES = new Set([
  'data_ingestion',
  'chunking',
  'embeddings',
  'vector_databases',
  'retrieval',
  'rag_architectures',
  'llm_layer',
  'evaluation',
]);

const STAGE_BY_CATEGORY = new Map<string, string>();
for (const stage of ARCHITECTURE_STAGES) {
  for (const cat of stage.categories) {
    STAGE_BY_CATEGORY.set(cat, stage.id);
  }
}

export function getStageIdForCategory(category?: string, slug?: string): string {
  if (slug) {
    const lower = slug.toLowerCase();
    for (const stage of ARCHITECTURE_STAGES) {
      if (stage.slugHints?.some((h) => lower.includes(h))) {
        return stage.id;
      }
    }
  }
  if (!category) return 'other';
  return STAGE_BY_CATEGORY.get(category) ?? 'other';
}

export function getStageLabel(stageId: string): string {
  if (stageId === 'other') return 'Supporting components';
  return ARCHITECTURE_STAGES.find((s) => s.id === stageId)?.label ?? stageId;
}

export function getStageShortLabel(stageId: string): string {
  if (stageId === 'other') return 'Other';
  return ARCHITECTURE_STAGES.find((s) => s.id === stageId)?.shortLabel ?? stageId;
}

export function orderedStageIds(): string[] {
  return [...ARCHITECTURE_STAGES.map((s) => s.id), 'other'];
}
