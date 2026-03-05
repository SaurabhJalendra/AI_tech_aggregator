'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface UsageStats {
  conversations_today: number;
  conversations_total: number;
  comparisons_total: number;
  tokens_used_today: number;
  cost_today_usd: number;
  tier: string;
}

interface RecentConversation {
  id: string;
  title: string;
  summary: string;
  message_count: number;
  created_at: string;
}

export default function DashboardHomePage() {
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [recent, setRecent] = useState<RecentConversation[]>([]);
  const [loading, setLoading] = useState(true);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

  useEffect(() => {
    Promise.allSettled([
      fetch(`${apiBase}/users/me`, {
        headers: { Authorization: 'Bearer dev@example.com' },
      }).then((r) => r.json()),
      fetch(`${apiBase}/sessions?limit=5`, {
        headers: { Authorization: 'Bearer dev@example.com' },
      }).then((r) => r.json()),
    ]).then(([statsResult, sessionsResult]) => {
      if (statsResult.status === 'fulfilled') {
        setStats(statsResult.value);
      }
      if (sessionsResult.status === 'fulfilled') {
        setRecent(sessionsResult.value?.sessions || []);
      }
      setLoading(false);
    });
  }, [apiBase]);

  return (
    <main className="p-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8">
          <h1 className="mb-2 text-3xl font-bold">Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Your AI advisor activity overview.
          </p>
        </div>

        {/* Stats cards */}
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Conversations Today"
            value={loading ? '...' : String(stats?.conversations_today || 0)}
          />
          <StatCard
            label="Total Conversations"
            value={loading ? '...' : String(stats?.conversations_total || 0)}
          />
          <StatCard
            label="Tokens Used Today"
            value={loading ? '...' : formatNumber(stats?.tokens_used_today || 0)}
          />
          <StatCard
            label="Current Tier"
            value={loading ? '...' : (stats?.tier || 'free').toUpperCase()}
            highlight
          />
        </div>

        {/* Quick actions */}
        <div className="mb-8">
          <h2 className="mb-4 text-lg font-semibold">Quick Actions</h2>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/advisor"
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              New Conversation
            </Link>
            <Link
              href="/explore"
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800"
            >
              Browse Modules
            </Link>
            <Link
              href="/history"
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800"
            >
              View History
            </Link>
          </div>
        </div>

        {/* Recent conversations */}
        <div>
          <h2 className="mb-4 text-lg font-semibold">Recent Conversations</h2>
          {loading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-16 animate-pulse rounded-lg bg-gray-100 dark:bg-gray-900" />
              ))}
            </div>
          ) : recent.length === 0 ? (
            <div className="rounded-lg border border-gray-200 p-8 text-center dark:border-gray-800">
              <p className="text-gray-500">No conversations yet</p>
              <Link href="/advisor" className="mt-2 inline-block text-sm text-blue-600 hover:underline">
                Start your first conversation
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {recent.map((conv) => (
                <Link
                  key={conv.id}
                  href={`/advisor?session=${conv.id}`}
                  className="block rounded-lg border border-gray-200 p-4 transition-colors hover:border-blue-300 dark:border-gray-800"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-medium">{conv.title || 'Untitled Conversation'}</h3>
                      {conv.summary && (
                        <p className="mt-1 text-sm text-gray-500">{conv.summary}</p>
                      )}
                    </div>
                    <span className="text-xs text-gray-400">
                      {conv.message_count} messages
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

function StatCard({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
      <p className="text-sm text-gray-500">{label}</p>
      <p
        className={`mt-1 text-2xl font-bold ${highlight ? 'text-blue-600' : ''}`}
      >
        {value}
      </p>
    </div>
  );
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}
