'use client';

import { useChatStore } from '@/stores/chatStore';

const SUGGESTIONS = [
  {
    icon: '🔍',
    title: 'Compare vector databases',
    prompt: 'Compare vector databases for my use case. I need something that scales well and has a good Python SDK.',
  },
  {
    icon: '🔗',
    title: 'Build me a RAG pipeline',
    prompt: 'Build me a RAG pipeline. Walk me through the best tools for ingestion, chunking, embedding, storage, and retrieval.',
  },
  {
    icon: '🧠',
    title: 'Help me choose an LLM',
    prompt: 'Help me choose an LLM. I need good reasoning capabilities with moderate cost and low latency.',
  },
  {
    icon: '🤖',
    title: 'Design an AI agent system',
    prompt: 'Design an AI agent system. I want autonomous agents that can use tools, maintain memory, and collaborate.',
  },
  {
    icon: '📐',
    title: 'What embedding model should I use?',
    prompt: 'What embedding model should I use? I need to embed documents for semantic search with good multilingual support.',
  },
  {
    icon: '🗺️',
    title: 'Show the full tech landscape',
    prompt: 'Show me the full technology landscape. Give me an overview of all the AI infrastructure categories and top tools in each.',
  },
];

export default function WelcomePanel() {
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isStreaming = useChatStore((s) => s.isStreaming);

  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className="max-w-2xl">
        <div className="mb-8 text-center">
          <h2 className="mb-2 text-2xl font-bold">
            AI Infrastructure Advisor
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Your guide to 86 tools across 18 categories. Compare technologies,
            design architectures, and find the right stack for your AI projects.
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s.title}
              onClick={() => {
                if (!isStreaming) sendMessage(s.prompt);
              }}
              disabled={isStreaming}
              className="flex items-start gap-3 rounded-lg border border-gray-200 p-4 text-left transition-colors hover:border-blue-300 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:hover:border-blue-800 dark:hover:bg-blue-950"
            >
              <span className="mt-0.5 text-xl">{s.icon}</span>
              <span className="text-sm font-medium">{s.title}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
