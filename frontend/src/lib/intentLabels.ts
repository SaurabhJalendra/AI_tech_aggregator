/** Human-readable labels for advisor intent ids (clarification UI). */
export const INTENT_LABELS: Record<string, string> = {
  unknown: 'General infrastructure advice',
  ambiguous: 'Clarify the goal',
  module_code: 'Integration code for a module',
  architecture_review: 'Reviewing an architecture diagram',
  local_ai_stack: 'Local / self-hosted LLM and agent stack',
  rag_pipeline: 'Designing an end-to-end RAG pipeline',
  'category:vector_databases': 'Vector databases and similarity search',
  'category:embeddings': 'Embedding models and APIs',
  'category:chunking': 'Chunking and text splitting',
  'category:data_ingestion': 'Data ingestion and parsing',
  'category:retrieval': 'Retrieval and reranking',
  'category:llm_layer': 'LLM choice and APIs',
  'category:agent_systems': 'Agent frameworks and orchestration',
  'category:evaluation': 'Evaluation and benchmarks',
  'category:deployment': 'Deployment and hosting',
};

export function intentLabel(intentId: string): string {
  return INTENT_LABELS[intentId] || intentId.replace(/^category:/, '').replace(/_/g, ' ');
}
