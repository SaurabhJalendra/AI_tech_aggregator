import { create } from 'zustand';
import type { ChatMessage, PanelCommand } from '@/types/chat';
import { usePanelStore } from './panelStore';

interface ChatState {
  messages: ChatMessage[];
  sessionId: string | null;
  isStreaming: boolean;

  // Actions
  sendMessage: (content: string) => void;
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

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  sessionId: null,
  isStreaming: false,

  sendMessage: (content: string) => {
    const { addUserMessage, addAssistantMessage, sessionId, setIsStreaming } = get();

    addUserMessage(content);
    const assistantId = addAssistantMessage();
    setIsStreaming(true);

    const body = JSON.stringify({
      message: content,
      session_id: sessionId,
    });

    fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer dev@example.com',
      },
      body,
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
      })
      .catch((error) => {
        console.error('Chat stream error:', error);
        get().appendStreamChunk(
          assistantId,
          '\n\n*An error occurred. Please try again.*'
        );
        get().finishStreaming(assistantId);
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
    set({ messages: [], sessionId: null, isStreaming: false });
  },

  setIsStreaming: (streaming: boolean) => {
    set({ isStreaming: streaming });
  },
}));
