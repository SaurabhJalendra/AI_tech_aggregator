/** Panel types that the backend can instruct the frontend to render */
export type PanelType =
  | 'welcome'
  | 'architecture_diagram'
  | 'comparison_table'
  | 'comparison_chart'
  | 'code_preview'
  | 'module_detail'
  | 'recommendation'
  | 'document'
  | 'option_cards'
  | 'interactive_architecture'
  | 'code_project';

/** A clickable option card presented in the option_cards panel */
export interface OptionCard {
  id: string;
  label: string;
  description?: string;
  icon?: string;
  metadata?: Record<string, unknown>;
}

/** Canonical constraint slot (mirrors backend ConstraintSlot). */
export interface ConstraintSlot {
  value: string | number | boolean | string[];
  source: 'explicit' | 'inferred' | 'option_card' | 'accumulated' | 'default';
  confidence: number;
  raw_label?: string | null;
}

/** Canonical constraint memory (Phase-2). */
export interface ConstraintStatePayload {
  slots: Record<string, ConstraintSlot>;
  playbook_id?: string | null;
  version?: string;
}

/** Deterministic pipeline explain payload for LLM narration. */
export interface RecommendationExplainPayload {
  playbook_id?: string | null;
  shortlist?: string[];
  scores?: Record<string, number>;
  score_breakdowns?: Record<string, Record<string, number>>;
  applied_filters?: Array<{ slug: string; reason: string }>;
  /** Snapshot of slot values at explain time (derived from ConstraintState). */
  constraint_slots?: Record<string, unknown>;
  reasoning_steps?: string[];
}

/** Extra context sent with a chat turn for model reasoning, not user display */
export interface ClientContext {
  active_task?: string | null;
  awaiting_intent_clarification?: boolean;
  intent_alternatives?: string[];
  intent_alternative_labels?: string[];
  resolved_intent_id?: string;
  active_playbook_id?: string;
  intent_clarification_choice?: {
    intent_id: string;
    label: string;
  };
  current_panel?: PanelType;
  current_panel_data?: Record<string, unknown>;
  /** Canonical constraint memory — sole source for accumulated slots. */
  constraint_state?: ConstraintStatePayload;
  recommendation_explain?: RecommendationExplainPayload;
  advisor_trace?: Record<string, unknown>;
  focus_module_slug?: string;
  architecture_node?: {
    id?: string;
    label?: string;
    slug?: string;
    category?: string;
  };
  option_answer?: {
    question_id?: string;
    question?: string;
    answer_id: string;
    answer_label: string;
    metadata?: Record<string, unknown>;
  };
  consulting_profile?: ConsultingProfilePayload;
  consulting_continuity?: string;
  strategy_branch_id?: string;
  pin_current_strategy?: boolean;
  tradeoff_lever?: string;
  sandbox_posture?: string;
  compare_pin_ids?: string[];
}

/** A node in the interactive architecture diagram */
export interface ArchNode {
  id: string;
  label: string;
  slug?: string;
  category?: string;
  description?: string;
}

/** An edge in the interactive architecture diagram */
export interface ArchEdge {
  from: string;
  to: string;
  label?: string;
}

/** Per-node decision intelligence from deterministic pipeline (Phase 3C). */
export interface ArchitectureNodeDecision {
  category?: string;
  selection_reason: string;
  considered: Array<{
    slug: string;
    label: string;
    score?: number;
    outcome?: string;
  }>;
  rejected: Array<{
    slug: string;
    label: string;
    reason: string;
  }>;
  tradeoffs_accepted: string[];
  operational_implications: string;
  deployment_implications: string;
  scaling_implications: string;
  workload_fit: string;
  fit_strength?: 'strong' | 'solid' | 'moderate';
  operational_risk?: string;
}

/** Backend architecture_consulting block on interactive_architecture panel data. */
export interface ArchitectureConsultingPayload {
  playbook_id?: string | null;
  workload_framing?: string | null;
  scale_badge?: string | null;
  operational_complexity?: string | null;
  comparative_priority_line?: string | null;
  priorities?: string[];
  confidence?: {
    tone: 'high' | 'solid' | 'moderate';
    headline: string;
    explanation: string;
    evidence?: string[];
    strongest_evidence?: string;
    evidence_hierarchy?: Array<{ tier: string; label: string; detail: string }>;
  };
  deployment_rationale?: string | null;
  scaling_rationale?: string | null;
  node_decisions?: Record<string, ArchitectureNodeDecision>;
  adaptation?: {
    message: string;
    changed_slots: string[];
  } | null;
  evolution?: ArchitectureEvolution | null;
  continuity_framing?: string | null;
  scale_atmosphere?: 'prototype' | 'production' | 'enterprise' | string | null;
  evidence_hierarchy?: {
    strongest: string;
    items: Array<{ tier: string; label: string; detail: string }>;
  };
  operational_posture?: {
    scaling_pressure?: string;
    maintenance_complexity?: string;
    deployment_burden?: string;
    operational_risk?: string;
    observability_maturity?: string;
    production_readiness?: string;
  };
  proactive_insights?: string[];
  lifecycle_notes?: string[];
  decision_timeline?: Array<{ type: string; title: string; detail: string }>;
  simulation?: {
    scenario_id: string;
    label: string;
    slot_updates: Record<string, unknown>;
    narrative: string;
  };
  /** Cross-session consulting relationship line */
  consulting_continuity?: string | null;
  /** Future-oriented strategic forecasts */
  strategic_forecasts?: StrategicForecast[];
  /** Subtle operational stress indicators (consulting-grade) */
  operational_stress?: OperationalStressIndicators;
  /** Explorable strategy branches */
  strategy_branches?: StrategyBranch[];
  /** True side-by-side infrastructure strategy comparison */
  strategy_comparison?: StrategyComparisonPayload;
  /** Persisted evolution timeline entries */
  evolution_history?: EvolutionHistoryEntry[];
  /** Phase 6 — organizational consulting */
  organizational_intelligence?: {
    insights?: string[];
    operational_capability?: string;
    ownership_burden?: string;
  };
  lifecycle_intelligence?: {
    notes?: string[];
    migration_pressure?: string;
    maintainability_trend?: string;
  };
  cost_evolution?: {
    trajectories?: Array<{ title: string; insight: string }>;
    cost_posture?: string;
  };
  ecosystem_evolution?: {
    insights?: string[];
    stability?: string;
    lock_in_risk?: string;
  };
  confidence_calibration?: {
    tone?: string;
    headline?: string;
    explanation?: string;
    uncertainty_zones?: string[];
  };
  tradeoff_simulator?: Array<{ id: string; label: string; tradeoff: string; active?: boolean }>;
  architecture_sandbox?: {
    postures?: Array<{ id: string; label: string }>;
    active_posture?: string | null;
  };
  strategic_timeline?: Array<{ type: string; title: string; detail: string; at?: string | null }>;
  strategy_workspace?: { pinned?: PinnedStrategy[]; count?: number };
  multi_strategy_overview?: MultiStrategyOverview;
  simulation_reasoning?: {
    scenario?: string;
    organizational_note?: string | null;
    lifecycle_note?: string | null;
    deterministic?: boolean;
  };
}

export interface PinnedStrategy {
  id: string;
  title: string;
  selections?: Record<string, string>;
  captured_at?: string;
}

export interface MultiStrategyOverview {
  theme: string;
  strategies: Array<{
    pin_id?: string;
    title?: string;
    comparative_priority_line?: string;
    operational_posture?: Record<string, string>;
    cost_evolution?: { trajectories?: Array<{ title: string; insight: string }> };
    organizational?: { insights?: string[] };
  }>;
  consulting_summary?: string;
}

export interface StrategicForecast {
  horizon: string;
  title: string;
  insight: string;
}

export interface OperationalStressIndicators {
  scaling_pressure?: string;
  retrieval_bottleneck_risk?: string;
  operational_fragility?: string;
  deployment_pressure?: string;
  latency_stress?: string;
  consulting_note?: string;
}

export interface StrategyBranch {
  id: string;
  label: string;
  summary: string;
  slot_preview: Record<string, unknown>;
  operational_consequence: string;
  future_tradeoff: string;
}

export interface StrategyComparisonDimension {
  dimension: string;
  left: string;
  right: string;
  insight: string;
}

export interface StrategyComparisonPayload {
  theme: string;
  left_label: string;
  right_label: string;
  dimensions: StrategyComparisonDimension[];
  consulting_summary?: string;
  left_architecture?: Record<string, unknown>;
  right_architecture?: Record<string, unknown>;
}

export interface EvolutionHistoryEntry {
  id: string;
  title: string;
  summary?: string | null;
  selections?: Record<string, string>;
  transition_reason?: string | null;
  created_at?: string | null;
}

/** Cross-session strategic consulting memory */
export interface ConsultingProfilePayload {
  slots?: Record<string, { value: unknown; source?: string }>;
  infrastructure_direction?: string | null;
}

export interface ArchitectureComparisonBaseline {
  title?: string;
  nodes: ArchNode[];
  edges?: ArchEdge[];
  selections?: Record<string, string>;
}

export interface ArchitectureEvolution {
  replacements: Array<{
    stage: string;
    stage_label: string;
    from_slug: string;
    from_label: string;
    to_slug: string;
    to_label: string;
  }>;
  changed_node_ids: string[];
  summary: string;
}

/** Command sent from the assistant (via SSE) to control the right-hand panel */
export interface PanelCommand {
  action: 'render' | 'update' | 'clear';
  panel: PanelType;
  data: Record<string, unknown>;
  title?: string;
  /** Set by deterministic planner panels (vs LLM tool output). */
  source?: 'planner' | string;
}

/** Tool activity indicator shown during assistant streaming */
export interface ToolActivity {
  tool: string;
  status: 'running' | 'complete';
  message?: string;
}

/** A single chat message in the conversation */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  panelCommands?: PanelCommand[];
  toolActivities?: ToolActivity[];
  timestamp: Date;
}

/** Shape of the SSE events streamed from the backend */
export interface SSEEvent {
  event: 'text' | 'panel_command' | 'tool_activity' | 'done' | 'error' | 'meta' | 'keepalive';
  data: string; // JSON-encoded payload
}

/** Payload for the text SSE event */
export interface TextEventData {
  content: string;
}

/** Payload for the panel_command SSE event */
export interface PanelCommandEventData {
  command: PanelCommand;
}

/** Payload for the error SSE event */
export interface ErrorEventData {
  message: string;
  code?: string;
}

/** Request body sent to POST /api/chat */
export interface ChatRequest {
  message: string;
  session_id?: string;
  client_context?: ClientContext;
}

/** Conversation session metadata */
export interface ConversationSession {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
}
