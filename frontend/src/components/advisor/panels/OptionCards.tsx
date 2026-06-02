'use client';

import { useChatStore } from '@/stores/chatStore';
import type { OptionCard } from '@/types/chat';

const ICON_MAP: Record<string, string> = {
  building: '🏢', enterprise: '🏢', headphones: '🎧', support: '🎧',
  book: '📚', research: '📚', code: '💻', technical: '💻',
  shield: '🛡️', legal: '⚖️', lock: '🔒', folder: '📁',
  cloud: '☁️', experiment: '🧪', beaker: '🧪', growth: '🚀', rocket: '🚀', other: '📋',
  document: '📄', search: '🔍', database: '🗄️', brain: '🧠',
  coin: '💸', scale: '⚖️', bolt: '⚡', tools: '🛠️', split: '🔀',
  user: '👤', team: '👥', platform: '🏗️',
};

function resolveIcon(icon?: string): string {
  if (!icon) return '';
  // If it's already an emoji (starts with non-ASCII), return as-is
  if (icon.charCodeAt(0) > 127) return icon;
  return ICON_MAP[icon.toLowerCase()] || '📌';
}

interface OptionCardsProps {
  data: Record<string, unknown>;
}

export default function OptionCards({ data }: OptionCardsProps) {
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isStreaming = useChatStore((s) => s.isStreaming);

  const question = (data.question as string) || '';
  const questionId =
    (data.question_id as string | undefined) ||
    (data.questionId as string | undefined);
  const options = (data.options as OptionCard[]) || [];

  const handleSelect = (option: OptionCard) => {
    if (isStreaming) return;
    sendMessage(option.label, {
      option_answer: {
        question_id: questionId,
        question,
        answer_id: option.id,
        answer_label: option.label,
        metadata: option.metadata,
      },
    });
  };

  const questionHeadingId = questionId
    ? `option-question-${questionId}`
    : 'option-question-heading';

  return (
    <div className="flex h-full flex-col p-6">
      {question && (
        <h2
          id={questionHeadingId}
          className="mb-6 text-xl font-semibold text-gray-900 dark:text-gray-100"
        >
          {question}
        </h2>
      )}

      <div
        role="group"
        aria-labelledby={question ? questionHeadingId : undefined}
        aria-label={question ? undefined : 'Answer options'}
        className="grid gap-3 sm:grid-cols-2"
      >
        {options.map((option) => (
          <button
            key={option.id}
            type="button"
            onClick={() => handleSelect(option)}
            disabled={isStreaming}
            aria-label={
              option.description
                ? `${option.label}. ${option.description}`
                : option.label
            }
            className="group flex flex-col items-start gap-2 rounded-xl border-2 border-gray-200 bg-white p-5 text-left transition-all hover:border-blue-500 hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-blue-400"
          >
            {option.icon && (
              <span className="text-2xl">{resolveIcon(option.icon)}</span>
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
