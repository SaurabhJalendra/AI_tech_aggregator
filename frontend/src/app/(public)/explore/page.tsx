'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import type { ModuleSummary, CategoryResponse } from '@/types/module';

const STATUS_COLORS: Record<string, string> = {
  stable: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  emerging: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  experimental: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
};

const PRICING_LABELS: Record<string, string> = {
  open_source: 'Open Source',
  freemium: 'Freemium',
  paid: 'Paid',
  usage_based: 'Usage Based',
  enterprise: 'Enterprise',
};

function ModuleCard({ module }: { module: ModuleSummary }) {
  return (
    <Link
      href={`/modules/${module.slug}`}
      className="group flex flex-col rounded-lg border border-gray-200 p-6 transition-all hover:border-blue-300 hover:shadow-md dark:border-gray-800 dark:hover:border-blue-700"
    >
      <div className="mb-3 flex items-start justify-between">
        <h3 className="text-lg font-semibold group-hover:text-blue-600 dark:group-hover:text-blue-400">
          {module.name}
        </h3>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[module.status] || 'bg-gray-100 text-gray-700'}`}
        >
          {module.status}
        </span>
      </div>

      {module.tagline && (
        <p className="mb-4 flex-1 text-sm text-gray-600 dark:text-gray-400">
          {module.tagline}
        </p>
      )}

      <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-500">
        <span className="rounded bg-gray-100 px-2 py-1 dark:bg-gray-800">
          {module.category.replace(/_/g, ' ')}
        </span>
        {module.pricing_model && (
          <span>{PRICING_LABELS[module.pricing_model] || module.pricing_model}</span>
        )}
      </div>
    </Link>
  );
}

export default function ExplorePage() {
  const [modules, setModules] = useState<ModuleSummary[]>([]);
  const [categories, setCategories] = useState<CategoryResponse[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

  useEffect(() => {
    fetch(`${apiBase}/modules/categories`)
      .then((res) => (res.ok ? res.json() : Promise.reject(res.statusText)))
      .then(setCategories)
      .catch(() => {});
  }, [apiBase]);

  useEffect(() => {
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (selectedCategory) params.set('category', selectedCategory);
    if (search) params.set('search', search);
    params.set('page_size', '50');

    const qs = params.toString();
    fetch(`${apiBase}/modules${qs ? `?${qs}` : ''}`)
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status}`);
        return res.json();
      })
      .then((data) => {
        setModules(data.modules || []);
        setLoading(false);
      })
      .catch((err) => {
        setError(`Failed to load modules: ${err.message}`);
        setLoading(false);
      });
  }, [apiBase, selectedCategory, search]);

  const filtered = modules.filter((m) => {
    if (search) {
      const q = search.toLowerCase();
      return (
        m.name.toLowerCase().includes(q) ||
        m.slug.toLowerCase().includes(q) ||
        (m.tagline && m.tagline.toLowerCase().includes(q)) ||
        m.category.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <main className="min-h-screen p-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8">
          <h1 className="mb-2 text-3xl font-bold">Explore Modules</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Browse {modules.length} AI/ML technologies across {categories.length} categories.
          </p>
        </div>

        {/* Search + Filters */}
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center">
          <input
            type="text"
            placeholder="Search modules..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm focus:border-blue-500 focus:outline-none dark:border-gray-700 dark:bg-gray-900"
          />
        </div>

        {/* Category pills */}
        <div className="mb-6 flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`rounded-full px-3 py-1 text-sm transition-colors ${
              !selectedCategory
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300'
            }`}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat.slug}
              onClick={() =>
                setSelectedCategory(selectedCategory === cat.slug ? null : cat.slug)
              }
              className={`rounded-full px-3 py-1 text-sm transition-colors ${
                selectedCategory === cat.slug
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300'
              }`}
            >
              {cat.name}
              {cat.module_count > 0 && (
                <span className="ml-1 opacity-60">({cat.module_count})</span>
              )}
            </button>
          ))}
        </div>

        {/* Module grid */}
        {loading ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="h-40 animate-pulse rounded-lg border border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900"
              />
            ))}
          </div>
        ) : error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
            <p className="font-medium">Error</p>
            <p className="text-sm">{error}</p>
            <p className="mt-2 text-xs">Make sure the backend is running on {apiBase}</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded-lg border border-gray-200 p-12 text-center dark:border-gray-800">
            <p className="text-lg text-gray-500">No modules found</p>
            <p className="mt-1 text-sm text-gray-400">
              Try adjusting your search or category filter.
            </p>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filtered.map((module) => (
              <ModuleCard key={module.slug} module={module} />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
