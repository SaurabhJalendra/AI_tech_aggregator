/** Module summary from GET /api/v1/modules */
export interface ModuleSummary {
  slug: string;
  name: string;
  category: string;
  subcategory?: string;
  tagline?: string;
  status: string;
  logo_url?: string;
  pricing_model?: string;
}

/** Comparison dimension score */
export interface DimensionScore {
  value: number;
  justification: string;
  normalized?: number;
}

/** Knowledge entry for a module */
export interface KnowledgeEntry {
  topic: string;
  content: string;
  tags: string[];
}

/** Code example for a module */
export interface CodeExample {
  title: string;
  language: string;
  code: string;
}

/** Benchmark result */
export interface BenchmarkResult {
  name: string;
  value: number;
  unit: string;
  context: string;
}

/** Relationship entry */
export interface ModuleRelationship {
  slug: string;
  note?: string;
  role?: string;
}

/** Full module detail from GET /api/v1/modules/{slug} */
export interface ModuleDetail {
  slug: string;
  name: string;
  category: string;
  subcategory?: string;
  status: string;
  version: string;

  // Identity
  tagline?: string;
  description: string;
  logo_url?: string;
  website?: string;
  documentation?: string;
  github_url?: string;
  license?: string;
  pricing_model?: string;

  // Data
  technical_specs: Record<string, unknown>;
  primary_use_cases: string[];
  supported_operations: string[];
  comparison_scores: Record<string, DimensionScore>;
  code_examples: CodeExample[];

  // Relationships
  alternatives: ModuleRelationship[];
  complements: ModuleRelationship[];
  pipeline_position?: string;

  // Knowledge
  knowledge_entries: KnowledgeEntry[];
  benchmarks: BenchmarkResult[];
}

/** Category from GET /api/v1/modules/categories */
export interface CategoryResponse {
  slug: string;
  name: string;
  description?: string;
  icon?: string;
  module_count: number;
}

/** Comparison dimension (axis for comparing modules) */
export interface ComparisonDimension {
  key: string;
  label: string;
  description: string;
  weight: number;
}

/** A single module's ranking across dimensions */
export interface ModuleRanking {
  module_slug: string;
  module_name: string;
  scores: Record<string, number>;
  overall_score: number;
  rank: number;
}

/** A single highlight point in a comparison */
export interface ComparisonHighlight {
  type: 'advantage' | 'disadvantage' | 'tie' | 'note';
  module_slug?: string;
  dimension?: string;
  text: string;
}

/** Full comparison result from POST /api/v1/compare */
export interface ComparisonResult {
  modules: string[];
  dimensions: ComparisonDimension[];
  matrix: Record<string, Record<string, number>>;
  rankings: ModuleRanking[];
  overall_ranking: string[];
  highlights: ComparisonHighlight[];
  recommendation: string;
}
