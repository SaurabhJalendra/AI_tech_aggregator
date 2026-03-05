'use client';

interface CodePreviewProps {
  data: Record<string, unknown>;
}

/**
 * CodePreview renders syntax-highlighted code snippets using Shiki.
 * Placeholder implementation.
 */
export default function CodePreview({ data }: CodePreviewProps) {
  const code = (data.code as string) || '// No code provided';
  const language = (data.language as string) || 'typescript';
  const filename = (data.filename as string) || '';

  return (
    <div className="p-6">
      <h2 className="mb-4 text-xl font-semibold">Code Preview</h2>

      {filename && (
        <div className="mb-2 text-sm text-gray-500 dark:text-gray-400">
          {filename}
        </div>
      )}

      <div className="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
        {/* Header bar */}
        <div className="flex items-center justify-between bg-gray-100 px-4 py-2 dark:bg-gray-800">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
            {language}
          </span>
          <button
            onClick={() => {
              navigator.clipboard.writeText(code).catch(() => {
                // clipboard write failed silently
              });
            }}
            className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            Copy
          </button>
        </div>

        {/* Code block — will use Shiki for syntax highlighting */}
        <pre className="overflow-x-auto bg-gray-50 p-4 text-sm dark:bg-gray-900">
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
}
