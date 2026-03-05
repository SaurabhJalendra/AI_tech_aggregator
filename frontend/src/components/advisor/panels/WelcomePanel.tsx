'use client';

/**
 * WelcomePanel is the default panel shown when no content has been
 * rendered yet. It provides quick-start suggestions for the user.
 */
export default function WelcomePanel() {
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
          <SuggestionCard
            title="Compare technologies"
            description="e.g., Compare LangChain vs LlamaIndex for RAG"
          />
          <SuggestionCard
            title="Architecture advice"
            description="e.g., Design a system for real-time AI inference"
          />
          <SuggestionCard
            title="Code examples"
            description="e.g., Show me how to set up a vector search with Pinecone"
          />
        </div>
      </div>
    </div>
  );
}

function SuggestionCard({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="cursor-pointer rounded-lg border border-gray-200 p-4 transition-colors hover:border-blue-300 hover:bg-blue-50 dark:border-gray-700 dark:hover:border-blue-800 dark:hover:bg-blue-950">
      <h3 className="font-medium">{title}</h3>
      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
        {description}
      </p>
    </div>
  );
}
