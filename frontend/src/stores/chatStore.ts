import { create } from 'zustand';
import type { ChatMessage, ClientContext, PanelCommand } from '@/types/chat';
import { usePanelStore } from './panelStore';

interface ChatState {
  messages: ChatMessage[];
  sessionId: string | null;
  activeTask: string | null;
  activeConstraints: Record<string, unknown>;
  isStreaming: boolean;
  abortController: AbortController | null;

  // Actions
  sendMessage: (content: string, clientContext?: ClientContext) => void;
  appendStreamChunk: (messageId: string, token: string) => void;
  addPanelCommand: (messageId: string, command: PanelCommand) => void;
  finishStreaming: (messageId: string) => void;
  setSessionId: (id: string) => void;
  addUserMessage: (content: string) => string;
  addAssistantMessage: () => string;
  clearMessages: () => void;
  setIsStreaming: (streaming: boolean) => void;
}

function generateId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

function isOptionAnswerContext(context?: ClientContext): boolean {
  return Boolean(context?.option_answer);
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  sessionId: null,
  activeTask: null,
  activeConstraints: {},
  isStreaming: false,
  abortController: null,

  sendMessage: (content: string, clientContext?: ClientContext) => {
    const { addUserMessage, addAssistantMessage, sessionId, setIsStreaming, abortController } = get();

    // Abort any previous in-flight request
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
    const activeTask =
      clientContext?.active_task ||
      (isOptionAnswerContext(clientContext) ? get().activeTask : content);
    const optionMetadata = clientContext?.option_answer?.metadata || {};
    const optionQuestionId = clientContext?.option_answer?.question_id;
    const optionAnswerId = clientContext?.option_answer?.answer_id;
    const activeConstraints = isOptionAnswerContext(clientContext)
      ? {
          ...get().activeConstraints,
          ...optionMetadata,
          ...(optionQuestionId && optionAnswerId
            ? { [optionQuestionId]: optionAnswerId }
            : {}),
        }
      : {};

    if (activeTask && activeTask !== get().activeTask) {
      set({ activeTask });
    }
    if (isOptionAnswerContext(clientContext) || Object.keys(get().activeConstraints).length > 0) {
      set({ activeConstraints });
    }

    const body = JSON.stringify({
      message: content,
      session_id: sessionId,
      client_context: {
        ...clientContext,
        active_task: activeTask,
        current_panel: clientContext?.current_panel || currentPanel,
        current_panel_data: clientContext?.current_panel_data || panelState.panelData,
        constraints: activeConstraints,
      },
    });

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

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6).trim();
              if (!dataStr || dataStr === '[DONE]') continue;

              try {
                const parsed = JSON.parse(dataStr);

                if (parsed.type === 'text' && parsed.content) {
                  get().appendStreamChunk(assistantId, parsed.content);
                }

                if (parsed.type === 'panel_command' && parsed.command) {
                  const command = parsed.command as PanelCommand;
                  get().addPanelCommand(assistantId, command);
                  usePanelStore.getState().renderPanel(command);
                }

                if (parsed.type === 'meta' && parsed.session_id && !get().sessionId) {
                  get().setSessionId(parsed.session_id);
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
                  get().appendStreamChunk(
                    assistantId,
                    `\n\n*${errorMessage}*`
                  );
                }

                if (parsed.type === 'done') {
                  // Stream complete
                }
              } catch {
                // Ignore malformed JSON lines
              }
            }
          }
        }

        get().finishStreaming(assistantId);
        set({ abortController: null });
      })
      .catch((error) => {
        if (error?.name === 'AbortError') return;
        console.error('Chat stream error:', error);
        get().appendStreamChunk(
          assistantId,
          '\n\n*An error occurred. Please try again.*'
        );
        get().finishStreaming(assistantId);
        set({ abortController: null });
      });
  },

  appendStreamChunk: (messageId: string, token: string) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId
          ? { ...msg, content: msg.content + token }
          : msg
      ),
    }));
  },

  addPanelCommand: (messageId: string, command: PanelCommand) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId
          ? {
              ...msg,
              panelCommands: [...(msg.panelCommands || []), command],
            }
          : msg
      ),
    }));
  },

  finishStreaming: (messageId: string) => {
    set((state) => ({
      isStreaming: false,
      messages: state.messages.map((msg) =>
        msg.id === messageId ? { ...msg } : msg
      ),
    }));
  },

  setSessionId: (id: string) => {
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
    set((state) => ({
      messages: [...state.messages, message],
    }));
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
    set((state) => ({
      messages: [...state.messages, message],
    }));
    return id;
  },

  clearMessages: () => {
    const { abortController } = get();
    if (abortController) {
      abortController.abort();
    }
    set({
      messages: [],
      sessionId: null,
      activeTask: null,
      activeConstraints: {},
      isStreaming: false,
      abortController: null,
    });
  },

  setIsStreaming: (streaming: boolean) => {
    set({ isStreaming: streaming });
  },
}));
