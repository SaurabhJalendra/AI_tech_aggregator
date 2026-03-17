'use client';

import { useChatStore } from '@/stores/chatStore';

const SUGGESTIONS = [
  {
    title: 'Compare technologies',
    description: 'e.g., Compare Pinecone vs Weaviate vs Qdrant for RAG',
    prompt: 'Compare Pinecone vs Weaviate vs Qdrant for a RAG application. I need a managed solution with good Python SDK support.',
  },
  {
    title: 'Architecture advice',
    description: 'e.g., Design a system for document Q&A',
    prompt: 'I want to build a document Q&A system. Help me choose the right stack for ingestion, chunking, embedding, storage, and retrieval.',
  },
  {
    title: 'Code examples',
    description: 'e.g., Show me how to set up a vector search with Pinecone',
    prompt: 'Show me how to set up vector search with Pinecone, including creating an index, upserting embeddings, and querying.',
  },
  {
    title: 'Evaluate options',
    description: 'e.g., What LLM should I use for my chatbot?',
    prompt: 'I\'m building a customer support chatbot. What LLM provider should I use? My budget is moderate and I need low latency.',
  },
];

export default function WelcomePanel() {
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isStreaming = useChatStore((s) => s.isStreaming);

  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className="max-w-lg text-center">
        <h2 className="mb-4 text-2xl font-bold">
          Welcome to AI Tech Advisor
        </h2>
        <p className="mb-8 text-gray-600 dark:text-gray-400">
          Ask me anything about AI/ML technologies. I can help you compare
          tools, design architectures, and find the right solutions for your
          needs.
        </p>
        <div className="grid gap-3 text-left">
          {SUGGESTIONS.map((s) => (
            <button
              key={s.title}
              onClick={() => {
                if (!isStreaming) sendMessage(s.prompt);
              }}
              disabled={isStreaming}
              className="cursor-pointer rounded-lg border border-gray-200 p-4 text-left transition-colors hover:border-blue-300 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:hover:border-blue-800 dark:hover:bg-blue-950"
            >
              <h3 className="font-medium">{s.title}</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {s.description}
              </p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
