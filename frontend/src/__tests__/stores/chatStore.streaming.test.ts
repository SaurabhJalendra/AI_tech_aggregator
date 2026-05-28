import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { useChatStore } from '@/stores/chatStore';

describe('chatStore streaming chaos', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useChatStore.setState({
      messages: [],
      sessionId: null,
      isStreaming: false,
      abortController: null,
      constraintState: null,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('finishOnce is idempotent under duplicate done events', async () => {
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(
          encoder.encode(
            'data: {"type":"text","content":"hi"}\n\n' +
              'data: {"type":"done"}\n\n' +
              'data: {"type":"done"}\n\n'
          )
        );
        controller.close();
      },
    });

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, body: stream })
    );

    useChatStore.getState().sendMessage('hello');
    await vi.runAllTimersAsync();

    expect(useChatStore.getState().isStreaming).toBe(false);
    expect(useChatStore.getState().abortController).toBeNull();
  });

  it('timeout abort finishes streaming', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        () =>
          new Promise(() => {
            /* never resolves */
          })
      )
    );

    useChatStore.getState().sendMessage('slow');
    expect(useChatStore.getState().isStreaming).toBe(true);

    await vi.advanceTimersByTimeAsync(180_000);
    expect(useChatStore.getState().isStreaming).toBe(false);
  });

  it('rapid cancel then retry clears streaming state', () => {
    useChatStore.setState({ isStreaming: true, abortController: new AbortController() });
    useChatStore.getState().stopStreaming();
    expect(useChatStore.getState().isStreaming).toBe(false);

    useChatStore.setState({ isStreaming: true, abortController: new AbortController() });
    useChatStore.getState().stopStreaming();
    expect(useChatStore.getState().isStreaming).toBe(false);
  });
});
