'use client';

import { useEffect, useState, use } from 'react';
import Link from 'next/link';
import type { ModuleDetail } from '@/types/module';

const DIMENSION_LABELS: Record<string, string> = {
  performance: 'Performance',
  scalability: 'Scalability',
  ease_of_use: 'Ease of Use',
  cost_efficiency: 'Cost Efficiency',
  community: 'Community',
  maturity: 'Maturity',
  flexibility: 'Flexibility',
  data_privacy: 'Data Privacy',
};

function ScoreBar({ label, score, justification }: { label: string; score: number; justification: string }) {
  return (
    <div className="group relative">
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="text-gray-700 dark:text-gray-300">{label}</span>
        <span className="font-mono font-medium">{score}/10</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
        <div
          className="h-full rounded-full bg-blue-500 transition-all"
          style={{ width: `${score * 10}%` }}
        />
      </div>
      <div className="pointer-events-none absolute -top-12 left-0 z-10 hidden w-64 rounded bg-gray-900 p-2 text-xs text-white shadow-lg group-hover:block dark:bg-gray-700">
        {justification}
      </div>
    </div>
  );
}

function CodeBlock({ title, language, code }: { title: string; language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-4 py-2 dark:border-gray-700 dark:bg-gray-800">
        <span className="text-sm font-medium">{title}</span>
        <div className="flex items-center gap-2">
          <span className="rounded bg-gray-200 px-2 py-0.5 text-xs dark:bg-gray-700">
            {language}
          </span>
          <button
            onClick={handleCopy}
            className="rounded px-2 py-0.5 text-xs text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>
      <pre className="overflow-x-auto bg-gray-900 p-4 text-sm text-gray-100">
        <code>{code}</code>
      </pre>
    </div>
  );
}

interface ModulePageProps {
  params: Promise<{ slug: string }>;
}

export default function ModulePage({ params }: ModulePageProps) {
  const { slug } = use(params);
  const [module, setModule] = useState<ModuleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

  useEffect(() => {
    setLoading(true);
    fetch(`${apiBase}/modules/${slug}`)
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status}`);
        return res.json();
      })
      .then((data) => {
        setModule(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(`Failed to load module: ${err.message}`);
        setLoading(false);
      });
  }, [apiBase, slug]);

  if (loading) {
    return (
      <main className="min-h-screen p-8">
        <div className="mx-auto max-w-4xl">
          <div className="h-8 w-48 animate-pulse rounded bg-gray-200 dark:bg-gray-800" />
          <div className="mt-4 h-4 w-96 animate-pulse rounded bg-gray-200 dark:bg-gray-800" />
          <div className="mt-8 space-y-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-lg bg-gray-100 dark:bg-gray-900" />
            ))}
          </div>
        </div>
      </main>
    );
  }

  if (error || !module) {
    return (
      <main className="min-h-screen p-8">
        <div className="mx-auto max-w-4xl">
          <Link href="/explore" className="mb-4 inline-block text-sm text-blue-600 hover:underline">
            &larr; Back to Explore
          </Link>
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-900 dark:bg-red-950">
            <p className="text-red-700 dark:text-red-400">{error || 'Module not found'}</p>
          </div>
        </div>
      </main>
    );
  }

  const scores = module.comparison_scores || {};

  return (
    <main className="min-h-screen p-8">
      <div className="mx-auto max-w-4xl">
        {/* Breadcrumb */}
        <Link href="/explore" className="mb-6 inline-block text-sm text-blue-600 hover:underline">
          &larr; Back to Explore
        </Link>

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-start gap-4">
            <div className="flex-1">
              <h1 className="mb-1 text-3xl font-bold">{module.name}</h1>
              {module.tagline && (
                <p className="text-lg text-gray-600 dark:text-gray-400">{module.tagline}</p>
              )}
            </div>
            <div className="flex flex-col items-end gap-2">
              <span
                className={`rounded-full px-3 py-1 text-sm font-medium ${
                  module.status === 'stable'
                    ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                    : module.status === 'emerging'
                      ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                      : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                }`}
              >
                {module.status}
              </span>
              <span className="text-xs text-gray-500">v{module.version}</span>
            </div>
          </div>

          {/* Meta badges */}
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="rounded bg-gray-100 px-2 py-1 text-xs dark:bg-gray-800">
              {module.category.replace(/_/g, ' ')}
            </span>
            {module.subcategory && (
              <span className="rounded bg-gray-100 px-2 py-1 text-xs dark:bg-gray-800">
                {module.subcategory}
              </span>
            )}
            {module.license && (
              <span className="rounded bg-gray-100 px-2 py-1 text-xs dark:bg-gray-800">
                {module.license}
              </span>
            )}
            {module.pricing_model && (
              <span className="rounded bg-blue-100 px-2 py-1 text-xs text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                {module.pricing_model.replace(/_/g, ' ')}
              </span>
            )}
          </div>

          {/* Links */}
          <div className="mt-4 flex gap-4">
            {module.website && (
              <a
                href={module.website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:underline"
              >
                Website
              </a>
            )}
            {module.documentation && (
              <a
                href={module.documentation}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:underline"
              >
                Documentation
              </a>
            )}
            {module.github_url && (
              <a
                href={module.github_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:underline"
              >
                GitHub
              </a>
            )}
          </div>
        </div>

        {/* Description */}
        <section className="mb-8">
          <h2 className="mb-3 text-xl font-semibold">Overview</h2>
          <div className="whitespace-pre-line text-gray-700 dark:text-gray-300">
            {module.description}
          </div>
        </section>

        {/* Use Cases & Operations */}
        {(module.primary_use_cases.length > 0 || module.supported_operations.length > 0) && (
          <section className="mb-8 grid gap-6 md:grid-cols-2">
            {module.primary_use_cases.length > 0 && (
              <div>
                <h2 className="mb-3 text-xl font-semibold">Use Cases</h2>
                <ul className="space-y-1">
                  {module.primary_use_cases.map((uc, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                      <span className="mt-1 text-blue-500">&#8226;</span>
                      {uc}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {module.supported_operations.length > 0 && (
              <div>
                <h2 className="mb-3 text-xl font-semibold">Operations</h2>
                <div className="flex flex-wrap gap-2">
                  {module.supported_operations.map((op, i) => (
                    <span
                      key={i}
                      className="rounded bg-gray-100 px-2 py-1 font-mono text-xs dark:bg-gray-800"
                    >
                      {op}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}

        {/* Comparison Scores */}
        {Object.keys(scores).length > 0 && (
          <section className="mb-8">
            <h2 className="mb-4 text-xl font-semibold">Scores</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              {Object.entries(scores).map(([key, dim]) => {
                const dimObj = typeof dim === 'object' && dim !== null ? (dim as { score?: number; value?: number; justification?: string }) : null;
                if (!dimObj) return null;
                const scoreVal = dimObj.score ?? dimObj.value ?? 5;
                return (
                  <ScoreBar
                    key={key}
                    label={DIMENSION_LABELS[key] || key}
                    score={scoreVal}
                    justification={dimObj.justification || ''}
                  />
                );
              })}
            </div>
          </section>
        )}

        {/* Knowledge Entries */}
        {module.knowledge_entries.length > 0 && (
          <section className="mb-8">
            <h2 className="mb-4 text-xl font-semibold">Knowledge Base</h2>
            <div className="space-y-4">
              {module.knowledge_entries.map((entry, i) => (
                <details
                  key={i}
                  className="group rounded-lg border border-gray-200 dark:border-gray-700"
                >
                  <summary className="cursor-pointer px-4 py-3 font-medium hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    {entry.topic}
                    {entry.tags && entry.tags.length > 0 && (
                      <span className="ml-2 text-xs text-gray-500">
                        {entry.tags.join(', ')}
                      </span>
                    )}
                  </summary>
                  <div className="border-t border-gray-200 px-4 py-3 dark:border-gray-700">
                    <div className="whitespace-pre-line text-sm text-gray-700 dark:text-gray-300">
                      {entry.content}
                    </div>
                  </div>
                </details>
              ))}
            </div>
          </section>
        )}

        {/* Code Examples */}
        {module.code_examples.length > 0 && (
          <section className="mb-8">
            <h2 className="mb-4 text-xl font-semibold">Code Examples</h2>
            <div className="space-y-4">
              {module.code_examples.map((ex, i) => (
                <CodeBlock key={i} title={ex.title} language={ex.language} code={ex.code} />
              ))}
            </div>
          </section>
        )}

        {/* Benchmarks */}
        {module.benchmarks.length > 0 && (
          <section className="mb-8">
            <h2 className="mb-4 text-xl font-semibold">Benchmarks</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="px-4 py-2 font-medium">Metric</th>
                    <th className="px-4 py-2 font-medium">Value</th>
                    <th className="px-4 py-2 font-medium">Unit</th>
                    <th className="px-4 py-2 font-medium">Context</th>
                  </tr>
                </thead>
                <tbody>
                  {module.benchmarks.map((b, i) => (
                    <tr
                      key={i}
                      className="border-b border-gray-100 dark:border-gray-800"
                    >
                      <td className="px-4 py-2 font-mono text-xs">{b.name}</td>
                      <td className="px-4 py-2 font-medium">{b.value}</td>
                      <td className="px-4 py-2 text-gray-500">{b.unit}</td>
                      <td className="px-4 py-2 text-gray-500">{b.context}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Relationships */}
        {(module.alternatives.length > 0 || module.complements.length > 0) && (
          <section className="mb-8">
            <h2 className="mb-4 text-xl font-semibold">Related Modules</h2>
            <div className="grid gap-6 md:grid-cols-2">
              {module.alternatives.length > 0 && (
                <div>
                  <h3 className="mb-2 text-sm font-medium text-gray-500 uppercase">Alternatives</h3>
                  <div className="space-y-2">
                    {module.alternatives.map((alt, i) => (
                      <Link
                        key={i}
                        href={`/modules/${alt.slug}`}
                        className="block rounded-lg border border-gray-200 p-3 text-sm hover:border-blue-300 dark:border-gray-700"
                      >
                        <span className="font-medium">{alt.slug}</span>
                        {alt.note && (
                          <span className="ml-2 text-gray-500">{alt.note}</span>
                        )}
                      </Link>
                    ))}
                  </div>
                </div>
              )}
              {module.complements.length > 0 && (
                <div>
                  <h3 className="mb-2 text-sm font-medium text-gray-500 uppercase">Complements</h3>
                  <div className="space-y-2">
                    {module.complements.map((comp, i) => (
                      <Link
                        key={i}
                        href={`/modules/${comp.slug}`}
                        className="block rounded-lg border border-gray-200 p-3 text-sm hover:border-blue-300 dark:border-gray-700"
                      >
                        <span className="font-medium">{comp.slug}</span>
                        {comp.role && (
                          <span className="ml-2 text-gray-500">- {comp.role}</span>
                        )}
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </section>
        )}

        {/* Pipeline Position */}
        {module.pipeline_position && (
          <section className="mb-8">
            <h2 className="mb-3 text-xl font-semibold">Pipeline Position</h2>
            <span className="rounded bg-blue-100 px-3 py-1 text-sm text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
              {module.pipeline_position}
            </span>
          </section>
        )}
      </div>
    </main>
  );
}
