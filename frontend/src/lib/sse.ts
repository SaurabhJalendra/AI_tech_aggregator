/**
 * SSE (Server-Sent Events) parser utility.
 *
 * Parses a raw SSE stream from a ReadableStream<Uint8Array> and invokes
 * typed callbacks for each event.
 */

export interface SSECallbacks {
  onToken?: (token: string) => void;
  onPanelCommand?: (command: Record<string, unknown>) => void;
  onSessionId?: (sessionId: string) => void;
  onDone?: () => void;
  onError?: (error: Error) => void;
}

/**
 * Parses SSE events from a ReadableStream. Each SSE frame follows the format:
 *
 *   event: <event-type>\n
 *   data: <json-payload>\n\n
 *
 * Or the simplified format used by many APIs:
 *
 *   data: <json-payload>\n\n
 */
export async function parseSSEStream(
  stream: ReadableStream<Uint8Array>,
  callbacks: SSECallbacks
): Promise<void> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let currentEvent = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        callbacks.onDone?.();
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      // Split on double newline (SSE frame boundary)
      const frames = buffer.split('\n\n');
      // The last element may be an incomplete frame
      buffer = frames.pop() || '';

      for (const frame of frames) {
        const lines = frame.split('\n');

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();

            if (dataStr === '[DONE]') {
              callbacks.onDone?.();
              continue;
            }

            try {
              const data = JSON.parse(dataStr);
              handleEvent(currentEvent, data, callbacks);
            } catch {
              // If JSON parsing fails, try treating it as a plain text token
              if (currentEvent === 'token' || !currentEvent) {
                callbacks.onToken?.(dataStr);
              }
            }

            // Reset event type after processing
            currentEvent = '';
          }
        }
      }
    }
  } catch (error) {
    callbacks.onError?.(error instanceof Error ? error : new Error(String(error)));
  } finally {
    reader.releaseLock();
  }
}

function handleEvent(
  eventType: string,
  data: Record<string, unknown>,
  callbacks: SSECallbacks
): void {
  switch (eventType) {
    case 'token':
      if (typeof data.token === 'string') {
        callbacks.onToken?.(data.token);
      }
      break;

    case 'panel_command':
      if (data.command) {
        callbacks.onPanelCommand?.(data.command as Record<string, unknown>);
      } else {
        callbacks.onPanelCommand?.(data);
      }
      break;

    case 'done':
      callbacks.onDone?.();
      break;

    case 'error':
      callbacks.onError?.(
        new Error(typeof data.message === 'string' ? data.message : 'Unknown SSE error')
      );
      break;

    default:
      // For events without an explicit type, try to infer from the data shape
      if (typeof data.token === 'string') {
        callbacks.onToken?.(data.token);
      } else if (data.command) {
        callbacks.onPanelCommand?.(data.command as Record<string, unknown>);
      } else if (typeof data.session_id === 'string') {
        callbacks.onSessionId?.(data.session_id);
      }
      break;
  }
}

/**
 * Helper: creates an AbortController with a timeout.
 * Useful for SSE connections that might hang.
 */
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
