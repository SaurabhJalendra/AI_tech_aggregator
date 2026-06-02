'use client';

import { useEffect, useState } from 'react';
import { codeToHtml } from 'shiki';
import { copyToClipboard } from '@/lib/copyToClipboard';

export interface CodeBlockData {
  title?: string;
  language?: string;
  code?: string;
  filename?: string;
  moduleName?: string;
}

interface CodeBlockProps {
  data: CodeBlockData;
  compact?: boolean;
}

export default function CodeBlock({ data, compact = false }: CodeBlockProps) {
  const code = data.code || '// No code provided';
  const language = data.language || 'python';
  const filename = data.filename || '';
  const blockTitle = data.title;

  const [highlightedHtml, setHighlightedHtml] = useState<string>('');
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'failed'>('idle');

  useEffect(() => {
    let cancelled = false;

    codeToHtml(code, {
      lang: language,
      theme: 'github-dark',
    })
      .then((html) => {
        if (!cancelled) setHighlightedHtml(html);
      })
      .catch(() => {
        // Highlighting failed; fall back to plain text
      });

    return () => {
      cancelled = true;
    };
  }, [code, language]);

  const handleCopy = async () => {
    const ok = await copyToClipboard(code);
    setCopyState(ok ? 'copied' : 'failed');
    window.setTimeout(() => setCopyState('idle'), 2000);
  };

  return (
    <div className={compact ? '' : 'p-6'}>
      {!compact && <h2 className="mb-4 text-xl font-semibold">Code Preview</h2>}
      {blockTitle && compact && (
        <p className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
          {blockTitle}
        </p>
      )}
      {filename && (
        <div className="mb-2 text-sm text-gray-500 dark:text-gray-400">{filename}</div>
      )}
      <div className="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between bg-gray-100 px-4 py-2 dark:bg-gray-800">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
            {language}
          </span>
          <button
            type="button"
            onClick={handleCopy}
            className="rounded px-2 py-0.5 text-xs font-medium text-gray-600 hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            {copyState === 'copied' ? 'Copied!' : copyState === 'failed' ? 'Copy failed' : 'Copy'}
          </button>
        </div>
        {highlightedHtml ? (
          <div
            className="max-h-72 overflow-auto text-sm [&_pre]:p-4"
            dangerouslySetInnerHTML={{ __html: highlightedHtml }}
          />
        ) : (
          <pre className="max-h-72 overflow-auto bg-gray-50 p-4 text-sm dark:bg-gray-900">
            <code>{code}</code>
          </pre>
        )}
      </div>
    </div>
  );
}
