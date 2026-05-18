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

/** Extra context sent with a chat turn for model reasoning, not user display */
export interface ClientContext {
  active_task?: string | null;
  current_panel?: PanelType;
  current_panel_data?: Record<string, unknown>;
  constraints?: Record<string, unknown>;
  option_answer?: {
    question_id?: string;
    question?: string;
    answer_id: string;
    answer_label: string;
    metadata?: Record<string, unknown>;
  };
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

/** Command sent from the assistant (via SSE) to control the right-hand panel */
export interface PanelCommand {
  action: 'render' | 'update' | 'clear';
  panel: PanelType;
  data: Record<string, unknown>;
  title?: string;
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
