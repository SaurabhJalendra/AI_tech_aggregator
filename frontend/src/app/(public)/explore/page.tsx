'use client';

import { useEffect, useState, useMemo } from 'react';
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

const CATEGORY_ICONS: Record<string, string> = {
  vector_databases: '🗄️',
  llm_providers: '🧠',
  embedding_models: '📐',
  orchestration_frameworks: '🔗',
  model_serving: '🚀',
  data_labeling: '🏷️',
  experiment_tracking: '📊',
  feature_stores: '📦',
  monitoring: '👁️',
  compute_platforms: '💻',
  data_pipelines: '🔄',
  annotation_tools: '✏️',
  automl: '⚡',
  model_registries: '📋',
  synthetic_data: '🧪',
  responsible_ai: '🛡️',
  edge_ai: '📱',
  ai_agents: '🤖',
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

function CategoryCard({
  category,
  isSelected,
  onClick,
}: {
  category: CategoryResponse;
  isSelected: boolean;
  onClick: () => void;
}) {
  const icon = category.icon || CATEGORY_ICONS[category.slug] || '📂';
  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center rounded-lg border p-4 text-center transition-all ${
        isSelected
          ? 'border-blue-500 bg-blue-50 shadow-sm dark:border-blue-600 dark:bg-blue-950'
          : 'border-gray-200 hover:border-blue-300 hover:shadow-sm dark:border-gray-800 dark:hover:border-blue-700'
      }`}
    >
      <span className="mb-2 text-2xl">{icon}</span>
      <span className="text-sm font-medium">{category.name}</span>
      <span className="mt-1 text-xs text-gray-500 dark:text-gray-400">
        {category.module_count} module{category.module_count !== 1 ? 's' : ''}
      </span>
    </button>
  );
}

export default function ExplorePage() {
  const [modules, setModules] = useState<ModuleSummary[]>([]);
  const [categories, setCategories] = useState<CategoryResponse[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const apiBase =
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    'http://localhost:8000';
  const apiUrl = `${apiBase}/api/v1`;

  // Fetch categories once
  useEffect(() => {
    fetch(`${apiUrl}/modules/categories`)
      .then((res) => (res.ok ? res.json() : Promise.reject(res.statusText)))
      .then(setCategories)
      .catch(() => {});
  }, [apiUrl]);

  // Fetch modules
  useEffect(() => {
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (selectedCategory) params.set('category', selectedCategory);
    params.set('per_page', '100');

    const qs = params.toString();
    fetch(`${apiUrl}/modules${qs ? `?${qs}` : ''}`)
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status}`);
        return res.json();
      })
      .then((data) => {
        setModules(data.modules || []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [apiUrl, selectedCategory]);

  // Client-side search filter
  const filtered = useMemo(() => {
    if (!search) return modules;
    const q = search.toLowerCase();
    return modules.filter(
      (m) =>
        m.name.toLowerCase().includes(q) ||
        m.slug.toLowerCase().includes(q) ||
        (m.tagline && m.tagline.toLowerCase().includes(q)) ||
        m.category.toLowerCase().includes(q)
    );
  }, [modules, search]);

  return (
    <main className="min-h-screen p-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8">
          <h1 className="mb-2 text-3xl font-bold">Explore Modules</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Browse {modules.length} AI/ML technologies across{' '}
            {categories.length} categories.
          </p>
        </div>

        {/* Search */}
        <div className="mb-6">
          <input
            type="text"
            placeholder="Search modules by name, category, or description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-900"
          />
        </div>

        {/* Category grid */}
        {categories.length > 0 && (
          <div className="mb-8">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Categories
            </h2>
            <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-9">
              {categories.map((cat) => (
                <CategoryCard
                  key={cat.slug}
                  category={cat}
                  isSelected={selectedCategory === cat.slug}
                  onClick={() =>
                    setSelectedCategory(
                      selectedCategory === cat.slug ? null : cat.slug
                    )
                  }
                />
              ))}
            </div>
            {selectedCategory && (
              <button
                onClick={() => setSelectedCategory(null)}
                className="mt-3 text-sm text-blue-600 hover:underline dark:text-blue-400"
              >
                Clear filter
              </button>
            )}
          </div>
        )}

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
            <p className="text-lg font-medium">Backend unavailable</p>
            <p className="mt-1 text-sm">
              Could not connect to the API. Make sure the backend is running.
            </p>
            <p className="mt-2 text-xs opacity-70">
              Tried: {apiUrl}
            </p>
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
