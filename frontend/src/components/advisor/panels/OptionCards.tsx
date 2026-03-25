'use client';

import { useChatStore } from '@/stores/chatStore';
import type { OptionCard } from '@/types/chat';

interface OptionCardsProps {
  data: Record<string, unknown>;
}

export default function OptionCards({ data }: OptionCardsProps) {
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isStreaming = useChatStore((s) => s.isStreaming);

  const question = (data.question as string) || '';
  const options = (data.options as OptionCard[]) || [];

  const handleSelect = (option: OptionCard) => {
    if (isStreaming) return;
    sendMessage(option.label);
  };

  return (
    <div className="flex h-full flex-col p-6">
      {question && (
        <h2 className="mb-6 text-xl font-semibold text-gray-900 dark:text-gray-100">
          {question}
        </h2>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        {options.map((option) => (
          <button
            key={option.id}
            onClick={() => handleSelect(option)}
            disabled={isStreaming}
            className="group flex flex-col items-start gap-2 rounded-xl border-2 border-gray-200 bg-white p-5 text-left transition-all hover:border-blue-500 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-blue-400"
          >
            {option.icon && (
              <span className="text-2xl">{option.icon}</span>
            )}
            <span className="text-sm font-semibold text-gray-900 group-hover:text-blue-600 dark:text-gray-100 dark:group-hover:text-blue-400">
              {option.label}
            </span>
            {option.description && (
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {option.description}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
