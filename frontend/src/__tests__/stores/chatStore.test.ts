import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from '@/stores/chatStore';

describe('chatStore', () => {
  beforeEach(() => {
    useChatStore.setState({
      messages: [],
      sessionId: null,
      activeTask: null,
      activeConstraints: {},
      isStreaming: false,
    });
  });

  it('should initialize with empty state', () => {
    const state = useChatStore.getState();
    expect(state.messages).toEqual([]);
    expect(state.sessionId).toBeNull();
    expect(state.activeTask).toBeNull();
    expect(state.activeConstraints).toEqual({});
    expect(state.isStreaming).toBe(false);
  });

  it('should add a user message', () => {
    const id = useChatStore.getState().addUserMessage('Hello');
    const state = useChatStore.getState();
    expect(state.messages).toHaveLength(1);
    expect(state.messages[0].id).toBe(id);
    expect(state.messages[0].role).toBe('user');
    expect(state.messages[0].content).toBe('Hello');
  });

  it('should add an assistant message', () => {
    const id = useChatStore.getState().addAssistantMessage();
    const state = useChatStore.getState();
    expect(state.messages).toHaveLength(1);
    expect(state.messages[0].id).toBe(id);
    expect(state.messages[0].role).toBe('assistant');
    expect(state.messages[0].content).toBe('');
  });

  it('should append stream chunks to a message', () => {
    const id = useChatStore.getState().addAssistantMessage();
    useChatStore.getState().appendStreamChunk(id, 'Hello');
    useChatStore.getState().appendStreamChunk(id, ' world');
    const state = useChatStore.getState();
    expect(state.messages[0].content).toBe('Hello world');
  });

  it('should set session ID', () => {
    useChatStore.getState().setSessionId('session-123');
    expect(useChatStore.getState().sessionId).toBe('session-123');
  });

  it('should clear messages', () => {
    useChatStore.getState().addUserMessage('test');
    useChatStore.getState().setSessionId('session-123');
    useChatStore.getState().clearMessages();

    const state = useChatStore.getState();
    expect(state.messages).toEqual([]);
    expect(state.sessionId).toBeNull();
    expect(state.activeTask).toBeNull();
    expect(state.activeConstraints).toEqual({});
    expect(state.isStreaming).toBe(false);
  });

  it('should add panel commands to a message', () => {
    const id = useChatStore.getState().addAssistantMessage();
    const command = {
      action: 'render' as const,
      panel: 'comparison_chart' as const,
      data: { modules: ['pinecone', 'weaviate'] },
      title: 'Comparison',
    };
    useChatStore.getState().addPanelCommand(id, command);

    const msg = useChatStore.getState().messages[0];
    expect(msg.panelCommands).toHaveLength(1);
    expect(msg.panelCommands![0].panel).toBe('comparison_chart');
  });

  it('should track streaming state', () => {
    useChatStore.getState().setIsStreaming(true);
    expect(useChatStore.getState().isStreaming).toBe(true);
    useChatStore.getState().setIsStreaming(false);
    expect(useChatStore.getState().isStreaming).toBe(false);
  });
});
