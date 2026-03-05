'use client';

import type { ChatMessage as ChatMessageType } from '@/types/chat';
import { clsx } from 'clsx';

interface ChatMessageProps {
  message: ChatMessageType;
}

/**
 * ChatMessage renders a single message bubble.
 * User messages are right-aligned, assistant messages are left-aligned.
 */
export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={clsx(
        'flex',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={clsx(
          'max-w-[85%] rounded-lg px-4 py-2 text-sm',
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
        )}
      >
        <div className="whitespace-pre-wrap break-words">
          {message.content}
        </div>
        {message.panelCommands && message.panelCommands.length > 0 && (
          <div className="mt-2 border-t border-gray-200 pt-2 dark:border-gray-700">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {message.panelCommands.length} panel update(s)
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
