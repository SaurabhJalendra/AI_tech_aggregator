/**
 * SSE (Server-Sent Events) parser utility.
 *
 * Parses a raw SSE stream from the backend. The backend emits events like:
 *   data: {"type": "text", "content": "..."}
 *   data: {"type": "panel_command", "command": {...}}
 *   data: {"type": "meta", "session_id": "..."}
 *   data: {"type": "done"}
 */

import type { PanelCommand } from '@/types/chat';

export interface SSECallbacks {
  onToken?: (token: string) => void;
  onPanelCommand?: (command: PanelCommand) => void;
  onSessionId?: (sessionId: string) => void;
  onDone?: () => void;
  onError?: (error: Error) => void;
}

export async function parseSSEStream(
  stream: ReadableStream<Uint8Array>,
  callbacks: SSECallbacks
): Promise<void> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        callbacks.onDone?.();
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;

        const dataStr = line.slice(6).trim();
        if (!dataStr || dataStr === '[DONE]') {
          callbacks.onDone?.();
          continue;
        }

        try {
          const data = JSON.parse(dataStr);

          switch (data.type) {
            case 'text':
              if (data.content) callbacks.onToken?.(data.content);
              break;
            case 'panel_command':
              if (data.command) callbacks.onPanelCommand?.(data.command);
              break;
            case 'meta':
              if (data.session_id) callbacks.onSessionId?.(data.session_id);
              break;
            case 'done':
              callbacks.onDone?.();
              break;
            case 'error':
              callbacks.onError?.(new Error(data.message || 'Unknown SSE error'));
              break;
          }
        } catch {
          // Ignore malformed lines
        }
      }
    }
  } catch (error) {
    callbacks.onError?.(error instanceof Error ? error : new Error(String(error)));
  } finally {
    reader.releaseLock();
  }
}

export function createTimeoutController(timeoutMs: number = 30000): {
  controller: AbortController;
  clear: () => void;
} {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  return {
    controller,
    clear: () => clearTimeout(timeoutId),
  };
}
