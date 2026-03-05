'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface Conversation {
  id: string;
  title: string;
  summary: string;
  message_count: number;
  total_tokens: number;
  total_cost_usd: number;
  created_at: string;
  updated_at: string;
}

export default function HistoryPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

  useEffect(() => {
    setLoading(true);
    fetch(`${apiBase}/sessions?page=${page}&page_size=${pageSize}`, {
      headers: { Authorization: 'Bearer dev@example.com' },
    })
      .then((r) => r.json())
      .then((data) => {
        setConversations(data?.sessions || []);
        setTotal(data?.total || 0);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [apiBase, page]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <main className="p-8">
      <div className="mx-auto max-w-4xl">
        <div className="mb-8">
          <h1 className="mb-2 text-3xl font-bold">Conversation History</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Review and continue your past advisor conversations.
          </p>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-20 animate-pulse rounded-lg bg-gray-100 dark:bg-gray-900" />
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <div className="rounded-lg border border-gray-200 p-12 text-center dark:border-gray-800">
            <p className="text-lg text-gray-500">No conversations yet</p>
            <p className="mt-1 text-sm text-gray-400">
              Start a conversation with the AI advisor to see it here.
            </p>
            <Link
              href="/advisor"
              className="mt-4 inline-block rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Start Conversation
            </Link>
          </div>
        ) : (
          <>
            <div className="space-y-3">
              {conversations.map((conv) => (
                <Link
                  key={conv.id}
                  href={`/advisor?session=${conv.id}`}
                  className="block rounded-lg border border-gray-200 p-4 transition-colors hover:border-blue-300 dark:border-gray-800 dark:hover:border-blue-700"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-medium">
                        {conv.title || 'Untitled Conversation'}
                      </h3>
                      {conv.summary && (
                        <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                          {conv.summary}
                        </p>
                      )}
                      <div className="mt-2 flex gap-4 text-xs text-gray-400">
                        <span>{conv.message_count} messages</span>
                        {conv.total_tokens > 0 && (
                          <span>{formatNumber(conv.total_tokens)} tokens</span>
                        )}
                        <span>{formatDate(conv.updated_at || conv.created_at)}</span>
                      </div>
                    </div>
                    <span className="ml-4 text-gray-400">&rarr;</span>
                  </div>
                </Link>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-6 flex items-center justify-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50 dark:border-gray-700"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-500">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50 dark:border-gray-700"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return d.toLocaleDateString();
  } catch {
    return dateStr;
  }
}
