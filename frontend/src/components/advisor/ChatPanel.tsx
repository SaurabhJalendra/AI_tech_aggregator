'use client';

import { useRef, useEffect } from 'react';
import { useChatStore } from '@/stores/chatStore';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';

/**
 * ChatPanel is the left sidebar (30% width) showing the conversation thread
 * and the message input.
 */
export default function ChatPanel() {
  const messages = useChatStore((s) => s.messages);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex w-[30%] min-w-[320px] flex-col border-r border-gray-200 dark:border-gray-800">
      {/* Messages area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-gray-400">
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
      </div>

      {/* Input area */}
      <ChatInput />
    </div>
  );
}
