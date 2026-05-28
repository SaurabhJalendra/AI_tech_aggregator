/** Map intent ids to Phase-1 playbook ids (mirrors backend playbooks.yaml). */
const INTENT_TO_PLAYBOOK: Record<string, string> = {
  'category:vector_databases': 'vector_db_comparison',
  rag_pipeline: 'rag_pipeline_design',
  module_code: 'module_code',
  architecture_review: 'architecture_review',
  local_ai_stack: 'local_ai_stack',
};

export function playbookForIntent(intentId: string): string | undefined {
  return INTENT_TO_PLAYBOOK[intentId];
}
