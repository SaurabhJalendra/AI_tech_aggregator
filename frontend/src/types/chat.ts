/** Panel types that the backend can instruct the frontend to render */
export type PanelType =
  | 'welcome'
  | 'architecture_diagram'
  | 'comparison_table'
  | 'comparison_chart'
  | 'code_preview'
  | 'module_detail'
  | 'recommendation'
  | 'document';

/** Command sent from the assistant (via SSE) to control the right-hand panel */
export interface PanelCommand {
  action: 'render' | 'update' | 'clear';
  panel: PanelType;
  data: Record<string, unknown>;
  title?: string;
}

/** A single chat message in the conversation */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  panelCommands?: PanelCommand[];
  timestamp: Date;
}

/** Shape of the SSE events streamed from the backend */
export interface SSEEvent {
  event: 'token' | 'panel_command' | 'done' | 'error';
  data: string; // JSON-encoded payload
}

/** Payload for the token SSE event */
export interface TokenEventData {
  token: string;
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
  context?: Record<string, unknown>;
}

/** Conversation session metadata */
export interface ConversationSession {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
}
