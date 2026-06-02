import { create } from 'zustand';
import { resolveOutgoingConstraintState } from '@/lib/constraintState';
import { useVisualIdentityStore } from '@/stores/visualIdentityStore';
import type {
  ChatMessage,
  ClientContext,
  ConstraintStatePayload,
  PanelCommand,
  RecommendationExplainPayload,
} from '@/types/chat';
import { playbookForIntent } from '@/lib/playbookMap';
import { usePanelStore } from './panelStore';

interface ChatState {
  messages: ChatMessage[];
  sessionId: string | null;
  activeTask: string | null;
  awaitingIntentClarification: boolean;
  intentAlternatives: string[];
  intentAlternativeLabels: string[];
  resolvedIntentId: string | null;
  activePlaybookId: string | null;
  constraintState: ConstraintStatePayload | null;
  lastAdvisorTrace: Record<string, unknown> | null;
  lastRecommendationExplain: RecommendationExplainPayload | null;
  consultingProfile: Record<string, unknown> | null;
  consultingContinuity: string | null;
  isStreaming: boolean;
  abortController: AbortController | null;

  sendMessage: (content: string, clientContext?: ClientContext) => void;
  sendClarificationChoice: (intentId: string, label: string) => void;
  appendStreamChunk: (messageId: string, token: string) => void;
  addPanelCommand: (messageId: string, command: PanelCommand) => void;
  finishStreaming: (messageId: string) => void;
  stopStreaming: () => void;
  setSessionId: (id: string) => void;
  addUserMessage: (content: string) => string;
  addAssistantMessage: () => string;
  clearMessages: () => void;
  setIsStreaming: (streaming: boolean) => void;
  setConstraintState: (state: ConstraintStatePayload | null) => void;
}

function generateId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

function isOptionAnswerContext(context?: ClientContext): boolean {
  return Boolean(context?.option_answer);
}

const SHORT_FOLLOWUP_MAX_LEN = 100;

function resolveActiveTask(
  content: string,
  clientContext: ClientContext | undefined,
  existingTask: string | null
): string | null {
  if (clientContext?.active_task) {
    return clientContext.active_task;
  }
  if (isOptionAnswerContext(clientContext) && existingTask) {
    return existingTask;
  }
  const trimmed = content.trim();
  if (existingTask && trimmed.length > 0 && trimmed.length < SHORT_FOLLOWUP_MAX_LEN) {
    return existingTask;
  }
  return trimmed || existingTask;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  sessionId: null,
  activeTask: null,
  awaitingIntentClarification: false,
  intentAlternatives: [],
  intentAlternativeLabels: [],
  resolvedIntentId: null,
  activePlaybookId: null,
  constraintState: null,
  lastAdvisorTrace: null,
  lastRecommendationExplain: null,
  consultingProfile: null,
  consultingContinuity: null,
  isStreaming: false,
  abortController: null,

  setConstraintState: (state) => {
    set({ constraintState: state });
  },

  sendMessage: (content: string, clientContext?: ClientContext) => {
    const { addUserMessage, addAssistantMessage, sessionId, setIsStreaming, abortController } = get();

    if (abortController) {
      abortController.abort();
    }

    const controller = new AbortController();
    set({ abortController: controller });

    addUserMessage(content);
    const assistantId = addAssistantMessage();
    setIsStreaming(true);

    const panelState = usePanelStore.getState();
    const currentPanel = panelState.currentPanel;
    const activeTask = resolveActiveTask(content, clientContext, get().activeTask);
    const activePlaybookId =
      clientContext?.active_playbook_id ?? get().activePlaybookId ?? undefined;

    const constraintState = resolveOutgoingConstraintState(
      get().constraintState,
      clientContext,
      activePlaybookId
    );

    if (activeTask && activeTask !== get().activeTask) {
      set({ activeTask });
    }
    if (constraintState) {
      set({ constraintState });
    }

    const awaitingClarification =
      clientContext?.awaiting_intent_clarification ?? get().awaitingIntentClarification;
    const resolvedIntentId =
      clientContext?.resolved_intent_id ?? get().resolvedIntentId ?? undefined;

    const body = JSON.stringify({
      message: content,
      session_id: sessionId,
      client_context: {
        ...clientContext,
        active_task: activeTask,
        awaiting_intent_clarification: awaitingClarification,
        intent_alternatives: clientContext?.intent_alternatives ?? get().intentAlternatives,
        resolved_intent_id: resolvedIntentId,
        active_playbook_id: activePlaybookId,
        current_panel: clientContext?.current_panel || currentPanel,
        current_panel_data: clientContext?.current_panel_data || panelState.panelData,
        constraint_state: constraintState ?? undefined,
        consulting_profile: clientContext?.consulting_profile ?? get().consultingProfile ?? undefined,
        consulting_continuity: clientContext?.consulting_continuity ?? get().consultingContinuity ?? undefined,
        option_answer: clientContext?.option_answer,
      },
    });

    const STREAM_TIMEOUT_MS = 180_000;
    let streamFinished = false;
    const finishOnce = () => {
      if (streamFinished) return;
      streamFinished = true;
      get().finishStreaming(assistantId);
      set({ abortController: null });
    };

    const processSseLine = (line: string) => {
      if (!line.startsWith('data: ')) return;
      const dataStr = line.slice(6).trim();
      if (!dataStr || dataStr === '[DONE]') return;

      try {
        const parsed = JSON.parse(dataStr);

        if (parsed.type === 'text' && parsed.content) {
          get().appendStreamChunk(assistantId, parsed.content);
        }

        if (parsed.type === 'panel_command' && parsed.command) {
          const command = parsed.command as PanelCommand;
          get().addPanelCommand(assistantId, command);
          usePanelStore.getState().renderPanel(command);
          set({ awaitingIntentClarification: false, intentAlternatives: [] });
          if (
            command.panel === 'option_cards' ||
            (command.panel === 'interactive_architecture' && command.source === 'planner')
          ) {
            finishOnce();
          }
        }

        if (parsed.type === 'done') {
          finishOnce();
        }

        if (parsed.type === 'meta') {
          if (parsed.session_id) {
            const prev = get().sessionId;
            if (!prev) {
              get().setSessionId(parsed.session_id);
            } else if (prev !== parsed.session_id) {
              useVisualIdentityStore.getState().bindSession(parsed.session_id);
              get().setSessionId(parsed.session_id);
            }
          }
          if (parsed.awaiting_intent_clarification) {
            set({
              awaitingIntentClarification: true,
              intentAlternatives: Array.isArray(parsed.intent_alternatives)
                ? parsed.intent_alternatives
                : [],
              intentAlternativeLabels: Array.isArray(parsed.intent_alternative_labels)
                ? parsed.intent_alternative_labels
                : [],
            });
          }
          if (parsed.resolved_intent_id) {
            set({ resolvedIntentId: parsed.resolved_intent_id });
          }
          if (parsed.active_playbook_id) {
            set({ activePlaybookId: parsed.active_playbook_id });
          }
          if (parsed.advisor_trace) {
            set({ lastAdvisorTrace: parsed.advisor_trace });
          }
          if (parsed.recommendation_explain) {
            set({ lastRecommendationExplain: parsed.recommendation_explain });
          }
          if (parsed.constraint_state) {
            const incoming = parsed.constraint_state as ConstraintStatePayload;
            const prior = get().constraintState;
            set({
              constraintState: prior
                ? {
                    ...prior,
                    slots: { ...prior.slots, ...(incoming.slots || {}) },
                    playbook_id: incoming.playbook_id ?? prior.playbook_id,
                  }
                : incoming,
            });
          }
          if (parsed.consulting_profile) {
            set({ consultingProfile: parsed.consulting_profile as Record<string, unknown> });
          }
          if (parsed.consulting_continuity) {
            set({ consultingContinuity: parsed.consulting_continuity });
          }
        }

        if (parsed.type === 'tool_activity') {
          const activity = parsed as unknown as { tool: string; status: string; message?: string };
          set((state) => ({
            messages: state.messages.map((msg) =>
              msg.id === assistantId
                ? {
                    ...msg,
                    toolActivities: [
                      ...(msg.toolActivities || []),
                      {
                        tool: activity.tool,
                        status: activity.status as 'running' | 'complete',
                        message: activity.message,
                      },
                    ],
                  }
                : msg
            ),
          }));
        }

        if (parsed.type === 'error') {
          const errorMessage =
            parsed.content || parsed.message || 'The advisor returned an error.';
          get().appendStreamChunk(assistantId, `\n\n*${errorMessage}*`);
          finishOnce();
        }
      } catch {
        // Ignore malformed JSON lines
      }
    };

    const timeoutId = window.setTimeout(() => {
      if (get().isStreaming) {
        controller.abort();
        get().appendStreamChunk(
          assistantId,
          '\n\n*The request timed out. Click Stop or try again.*'
        );
        finishOnce();
      }
    }, STREAM_TIMEOUT_MS);

    fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer dev@example.com',
      },
      body,
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok || !response.body) {
          throw new Error(`Chat request failed: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              processSseLine(line);
            }
          }
        } finally {
          window.clearTimeout(timeoutId);
          finishOnce();
        }
      })
      .catch((error) => {
        window.clearTimeout(timeoutId);
        if (error?.name === 'AbortError') {
          finishOnce();
          return;
        }
        console.error('Chat stream error:', error);
        get().appendStreamChunk(assistantId, '\n\n*An error occurred. Please try again.*');
        finishOnce();
      });
  },

  appendStreamChunk: (messageId: string, token: string) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId ? { ...msg, content: msg.content + token } : msg
      ),
    }));
  },

  addPanelCommand: (messageId: string, command: PanelCommand) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId
          ? { ...msg, panelCommands: [...(msg.panelCommands || []), command] }
          : msg
      ),
    }));
  },

  finishStreaming: (messageId: string) => {
    set((state) => ({
      isStreaming: false,
      abortController: null,
      messages: state.messages.map((msg) => (msg.id === messageId ? { ...msg } : msg)),
    }));
  },

  stopStreaming: () => {
    const { abortController, messages } = get();
    if (abortController) {
      abortController.abort();
    }
    const lastAssistant = [...messages].reverse().find((m) => m.role === 'assistant');
    if (lastAssistant) {
      get().finishStreaming(lastAssistant.id);
    } else {
      set({ isStreaming: false, abortController: null });
    }
  },

  setSessionId: (id: string) => {
    useVisualIdentityStore.getState().bindSession(id);
    set({ sessionId: id });
  },

  addUserMessage: (content: string) => {
    const id = generateId();
    const message: ChatMessage = {
      id,
      role: 'user',
      content,
      timestamp: new Date(),
    };
    set((state) => ({ messages: [...state.messages, message] }));
    return id;
  },

  addAssistantMessage: () => {
    const id = generateId();
    const message: ChatMessage = {
      id,
      role: 'assistant',
      content: '',
      panelCommands: [],
      timestamp: new Date(),
    };
    set((state) => ({ messages: [...state.messages, message] }));
    return id;
  },

  clearMessages: () => {
    const { abortController } = get();
    if (abortController) {
      abortController.abort();
    }
    useVisualIdentityStore.getState().reset();
    set({
      messages: [],
      sessionId: null,
      activeTask: null,
      awaitingIntentClarification: false,
      intentAlternatives: [],
      intentAlternativeLabels: [],
      resolvedIntentId: null,
      activePlaybookId: null,
      constraintState: null,
      lastAdvisorTrace: null,
      lastRecommendationExplain: null,
      isStreaming: false,
      abortController: null,
    });
  },

  sendClarificationChoice: (intentId: string, label: string) => {
    const { activeTask, sendMessage } = get();
    const playbookId = playbookForIntent(intentId);
    set({
      awaitingIntentClarification: false,
      resolvedIntentId: intentId,
      activePlaybookId: playbookId ?? null,
      intentAlternatives: [],
      intentAlternativeLabels: [],
    });
    sendMessage(label, {
      active_task: activeTask ?? label,
      awaiting_intent_clarification: false,
      intent_clarification_choice: { intent_id: intentId, label },
      resolved_intent_id: intentId,
      active_playbook_id: playbookId,
    });
  },

  setIsStreaming: (streaming: boolean) => {
    set({ isStreaming: streaming });
  },
}));
