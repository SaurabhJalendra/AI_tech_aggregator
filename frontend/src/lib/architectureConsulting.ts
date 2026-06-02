import { formatEntityLabel } from '@/lib/entityDisplay';
import { getStageIdForCategory, getStageLabel } from '@/lib/architectureStages';
import type { ArchNode } from '@/types/chat';

/** Consulting-facing labels for pipeline categories. */
const CATEGORY_CONSULTING_NAME: Record<string, string> = {
  data_ingestion: 'Document & data intake',
  chunking: 'Content preprocessing',
  embeddings: 'Semantic embedding',
  vector_databases: 'Semantic retrieval storage',
  retrieval: 'Hybrid retrieval',
  rag_architectures: 'RAG orchestration',
  llm_layer: 'Language generation',
  agent_systems: 'Agent orchestration',
  evaluation: 'Quality evaluation',
  deployment: 'Production deployment',
  caching: 'Response caching',
  workflow_orchestration: 'Workflow orchestration',
  security_compliance: 'Safety & compliance',
  search_discovery: 'Search & discovery',
  voice_conversational: 'Voice interface',
};

const CATEGORY_ROLE: Record<string, string> = {
  data_ingestion: 'Brings source documents into the pipeline',
  chunking: 'Prepares text for embedding and search',
  embeddings: 'Converts content into searchable vectors',
  vector_databases: 'Stores vectors for similarity search',
  retrieval: 'Finds relevant context for each query',
  rag_architectures: 'Connects retrieval to generation',
  llm_layer: 'Produces answers from retrieved context',
  agent_systems: 'Coordinates multi-step AI workflows',
  evaluation: 'Measures answer quality and drift',
  deployment: 'Runs the stack in production',
  caching: 'Reduces latency and repeated work',
  workflow_orchestration: 'Orchestrates pipeline stages',
};

/** Operational / workload-oriented one-liners for node cards. */
const CATEGORY_OPERATIONAL: Record<string, string> = {
  data_ingestion: 'Keeps ingestion dependable as document volume increases',
  chunking: 'Tuning layer — affects recall quality more than headline scale',
  embeddings: 'Foundation for semantic search under real query load',
  vector_databases: 'Well-suited for rapidly growing production retrieval workloads',
  retrieval: 'Balances recall and precision for production Q&A patterns',
  rag_architectures: 'Orchestrates evidence flow into grounded answers',
  llm_layer: 'Designed for reliable generation once context is retrieved',
  agent_systems: 'Supports multi-step automation beyond single-shot Q&A',
  evaluation: 'Makes quality visible before users feel regressions',
  deployment: 'Carries the stack into production with operable boundaries',
  caching: 'Supporting layer — trims repeat cost and latency',
};

const SLUG_ROLE_OVERRIDES: Record<string, string> = {
  reranking_models: 'Result relevance optimization',
  hybrid_search: 'Combines keyword and vector search',
  query_transformation: 'Refines queries before retrieval',
};

export function getConsultingNodeTitle(node: ArchNode): string {
  if (node.slug && SLUG_ROLE_OVERRIDES[node.slug]) {
    return SLUG_ROLE_OVERRIDES[node.slug];
  }
  if (node.category && CATEGORY_CONSULTING_NAME[node.category]) {
    return CATEGORY_CONSULTING_NAME[node.category];
  }
  return node.label;
}

export function getNodeRoleLine(
  node: ArchNode,
  importance: 'primary' | 'standard' | 'supporting' = 'standard'
): string {
  if (importance === 'primary' && node.category && CATEGORY_OPERATIONAL[node.category]) {
    return CATEGORY_OPERATIONAL[node.category];
  }
  if (node.slug && SLUG_ROLE_OVERRIDES[node.slug]) return SLUG_ROLE_OVERRIDES[node.slug];
  if (node.category && CATEGORY_ROLE[node.category]) return CATEGORY_ROLE[node.category];
  if (node.description && node.description.length < 90) return node.description;
  if (importance === 'supporting') {
    return 'Supporting layer — refines quality without changing the core architecture story';
  }
  return 'Core component in your recommended architecture';
}

export function humanizeEdgeLabel(label?: string): string | undefined {
  if (!label) return undefined;
  const lower = label.toLowerCase();
  if (lower.includes('embed')) return 'Vectors';
  if (lower.includes('chunk')) return 'Chunks';
  if (lower.includes('retrieve') || lower.includes('search')) return 'Context';
  if (lower.includes('rank') || lower.includes('rerank')) return 'Ranked results';
  if (lower.includes('generat') || lower.includes('llm')) return 'Answer';
  if (lower.includes('eval')) return 'Metrics';
  if (label.length <= 24) return label;
  return undefined;
}

export interface NodeConsultingProfile {
  consultingTitle: string;
  roleLine: string;
  stageLabel: string;
  whySelected: string;
  operationalNote: string;
  scalingNote: string;
  tradeoffNote: string | null;
  deploymentFit: string;
}

export function buildNodeConsultingProfile(node: ArchNode): NodeConsultingProfile {
  const stageId = getStageIdForCategory(node.category, node.slug);
  const stageLabel = getStageLabel(stageId);
  const name = formatEntityLabel(node.slug ?? node.label);
  const consultingTitle = getConsultingNodeTitle(node);
  const roleLine = getNodeRoleLine(node);

  const whySelected = node.description
    ? `${name} was selected because ${node.description.charAt(0).toLowerCase()}${node.description.slice(1)}`
    : `${name} fits the ${stageLabel.toLowerCase()} of your pipeline based on constraint-aware scoring and playbook rules.`;

  const operationalByCategory: Record<string, string> = {
    vector_databases:
      'Expect managed scaling for index growth; plan capacity for query volume and storage.',
    llm_layer: 'Token usage and latency drive cost — size context windows to your SLA.',
    retrieval: 'Tune recall vs precision; hybrid setups add operational tuning.',
    embeddings: 'Batch embedding jobs affect ingestion latency; cache where possible.',
    evaluation: 'Instrument early — quality regressions are easier to catch before production.',
  };

  const scalingByCategory: Record<string, string> = {
    vector_databases: 'Scales horizontally with sharding/replication when document count grows.',
    llm_layer: 'Scales with concurrent users; consider routing and caching for peaks.',
    data_ingestion: 'Parallelize ingestion workers for large corpora.',
    default: 'Designed for production workloads with room to grow as traffic increases.',
  };

  const tradeoffs: Record<string, string> = {
    vector_databases:
      'You trade some setup complexity for stronger semantic search at scale.',
    llm_layer: 'Higher capability models may increase cost versus smaller local models.',
    retrieval: 'More sophisticated retrieval adds tuning surface area.',
  };

  return {
    consultingTitle,
    roleLine,
    stageLabel,
    whySelected,
    operationalNote:
      operationalByCategory[node.category ?? ''] ??
      'Balances capability with reasonable day-two operational burden for your team.',
    scalingNote: scalingByCategory[node.category ?? ''] ?? scalingByCategory.default,
    tradeoffNote: tradeoffs[node.category ?? ''] ?? null,
    deploymentFit:
      stageId === 'storage_retrieval' || node.category === 'vector_databases'
        ? 'Fits retrieval-heavy RAG and semantic search workloads.'
        : stageId === 'rag_generation'
          ? 'Supports answer generation and orchestration at the center of the stack.'
          : 'Supports the operational flow of your recommended architecture.',
  };
}

/** Short stage descriptions for flow legend. */
export const STAGE_FLOW_DESCRIPTIONS: Record<string, string> = {
  data_processing: 'Source documents are prepared for search',
  embeddings: 'Content becomes vector representations',
  storage_retrieval: 'Relevant context is found and ranked',
  ranking: 'Results are re-ordered for relevance',
  rag_generation: 'Answers are generated from context',
  quality_ops: 'Quality and deployment are monitored',
  other: 'Supporting infrastructure',
};

export function getStageFlowDescription(stageId: string): string {
  return STAGE_FLOW_DESCRIPTIONS[stageId] ?? STAGE_FLOW_DESCRIPTIONS.other;
}
