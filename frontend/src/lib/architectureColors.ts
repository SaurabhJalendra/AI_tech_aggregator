/** Muted category colors — aligned with calm advisor theme. */

export interface CategoryStyle {
  fill: string;
  stroke: string;
  text: string;
  accent: string;
}

export const ARCH_CATEGORY_COLORS: Record<string, CategoryStyle> = {
  data_ingestion: { fill: '#eef2f6', stroke: '#94a3b8', text: '#334155', accent: '#64748b' },
  chunking: { fill: '#f3f0f7', stroke: '#a8a3b8', text: '#44403c', accent: '#78716c' },
  embeddings: { fill: '#f5f0e8', stroke: '#c4a484', text: '#57534e', accent: '#a8a29e' },
  vector_databases: { fill: '#edf3ef', stroke: '#8fa97b', text: '#3f4f3a', accent: '#6b7f62' },
  retrieval: { fill: '#eef3f4', stroke: '#7d98a1', text: '#334155', accent: '#64748b' },
  rag_architectures: { fill: '#f2f0f6', stroke: '#9d8fb8', text: '#44403c', accent: '#78716c' },
  llm_layer: { fill: '#eef1f6', stroke: '#7c8db5', text: '#334155', accent: '#64748b' },
  agent_systems: { fill: '#f4f0ee', stroke: '#b78b7a', text: '#44403c', accent: '#78716c' },
  evaluation: { fill: '#eef2f0', stroke: '#6f9f9a', text: '#334155', accent: '#64748b' },
  caching: { fill: '#f0f2f5', stroke: '#a4a0b8', text: '#334155', accent: '#64748b' },
  deployment: { fill: '#f2f2f4', stroke: '#94a3b8', text: '#334155', accent: '#64748b' },
  default: { fill: '#f1f3f5', stroke: '#cbd5e1', text: '#475569', accent: '#94a3b8' },
};

export function getArchCategoryStyle(category?: string): CategoryStyle {
  return ARCH_CATEGORY_COLORS[category || ''] ?? ARCH_CATEGORY_COLORS.default;
}
