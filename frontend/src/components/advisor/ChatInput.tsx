'use client';

import { useState, useCallback, useEffect, useRef, type KeyboardEvent } from 'react';
import { useChatStore } from '@/stores/chatStore';

const PLACEHOLDERS = [
  'Ask about vector databases...',
  'Compare Pinecone vs Qdrant...',
  'Build me a RAG pipeline...',
  'Help me choose an LLM...',
  'Design an AI agent system...',
];

/**
 * ChatInput provides the text input and send button at the bottom of the chat panel.
 * Features: auto-resize, stop button, character count, cycling placeholder.
 */
export default function ChatInput() {
  const [input, setInput] = useState('');
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const stopStreaming = useChatStore((s) => s.stopStreaming);

  // Cycle placeholder text
  useEffect(() => {
    const interval = setInterval(() => {
      setPlaceholderIndex((prev) => (prev + 1) % PLACEHOLDERS.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    const lineHeight = 24;
    const maxHeight = lineHeight * 6; // max 6 lines
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`;
  }, [input]);

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;
    sendMessage(trimmed);
    setInput('');
  }, [input, isStreaming, sendMessage]);

  const handleStop = useCallback(() => {
    stopStreaming();
  }, [stopStreaming]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  return (
    <div className="border-t border-[var(--border-subtle)] p-4">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={PLACEHOLDERS[placeholderIndex]}
            rows={1}
            className="w-full resize-none rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-panel)] px-3 py-2 pr-12 text-sm leading-6 text-[var(--foreground)] placeholder:text-[var(--text-muted)] focus:border-[var(--border-strong)] focus:outline-none focus:ring-1 focus:ring-[var(--border-strong)]"
          />
          {input.length > 500 && (
            <span className="absolute bottom-1.5 right-2 text-xs text-gray-400">
              {input.length}
            </span>
          )}
        </div>
        {isStreaming ? (
          <button
            onClick={handleStop}
            className="self-end rounded-lg border border-[var(--border-strong)] bg-[var(--surface-secondary)] px-4 py-2 text-sm font-medium text-[var(--foreground)] transition-colors hover:bg-[var(--surface-hover)]"
          >
            Stop
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="self-end rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-medium text-[var(--accent-foreground)] transition-colors hover:bg-[var(--accent-hover)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            Send
          </button>
        )}
      </div>
      <p className="mt-1.5 text-xs text-[var(--text-muted)]">
        Enter to send, Shift+Enter for new line
      </p>
    </div>
  );
}
