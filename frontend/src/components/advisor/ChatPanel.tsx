'use client';

import { useRef, useEffect } from 'react';
import { useChatStore } from '@/stores/chatStore';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import IntentClarification from './IntentClarification';
import ConstraintChipBar from './ConstraintChipBar';

/**
 * ChatPanel is the left sidebar (30% width) showing the conversation thread
 * and the message input.
 */
export default function ChatPanel() {
  const messages = useChatStore((s) => s.messages);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const scrollRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex h-full min-h-0 w-full flex-col border-r border-[var(--border-subtle)] bg-[var(--surface-panel)]">
      {/* Messages area */}
      <div
        ref={scrollRef}
        className="scrollbar-hidden flex-1 overflow-y-auto p-4 space-y-4"
      >
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-[var(--text-muted)]">
              Start a conversation with your AI advisor
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        {isStreaming && (
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-blue-500" />
            Thinking...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <ConstraintChipBar />
      <div className="border-t border-[var(--border-subtle)] px-4 pt-3">
        <IntentClarification />
      </div>

      {/* Input area — pinned to bottom of full-height panel */}
      <div className="mt-auto shrink-0">
        <ChatInput />
      </div>
    </div>
  );
}
