import Link from 'next/link';

const CATEGORIES = [
  { name: 'Data Ingestion', count: 6, icon: '📥' },
  { name: 'Chunking', count: 3, icon: '✂️' },
  { name: 'Embeddings', count: 6, icon: '🔢' },
  { name: 'Vector Databases', count: 10, icon: '🗄️' },
  { name: 'RAG Architectures', count: 3, icon: '🔍' },
  { name: 'LLMs', count: 14, icon: '🧠' },
  { name: 'Agent Systems', count: 7, icon: '🤖' },
  { name: 'Retrieval', count: 5, icon: '🔎' },
  { name: 'Evaluation', count: 8, icon: '📊' },
];

const FEATURES = [
  {
    title: 'AI-Powered Advisor',
    description:
      'Describe your use case and get personalized recommendations. The advisor cross-questions you to understand your needs before suggesting solutions.',
  },
  {
    title: 'Live Comparisons',
    description:
      'Compare technologies side-by-side across 8 dimensions with interactive charts. See strengths, weaknesses, and trade-offs at a glance.',
  },
  {
    title: 'Architecture Diagrams',
    description:
      'Get interactive architecture diagrams showing how components fit together. Click nodes to explore each technology in depth.',
  },
  {
    title: 'Starter Code',
    description:
      'Ready-to-use code examples for every module. Copy, paste, and start building your AI pipeline immediately.',
  },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-4">
        <span className="text-lg font-bold">AI Tech Aggregator</span>
        <div className="flex items-center gap-6">
          <Link href="/explore" className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">
            Explore
          </Link>
          <Link href="/pricing" className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white">
            Pricing
          </Link>
          <Link
            href="/advisor"
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Open Advisor
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex flex-col items-center px-8 pb-16 pt-24 text-center">
        <h1 className="mb-4 max-w-3xl text-5xl font-bold tracking-tight sm:text-6xl">
          Choose the right AI stack,{' '}
          <span className="text-blue-600">with confidence</span>
        </h1>
        <p className="mb-8 max-w-2xl text-lg text-gray-600 dark:text-gray-400">
          86 technologies across 18 categories. An AI advisor that cross-questions you,
          runs live comparisons, generates architecture diagrams, and produces starter code.
        </p>
        <div className="flex gap-4">
          <Link
            href="/advisor"
            className="rounded-lg bg-blue-600 px-8 py-3 text-lg font-semibold text-white shadow-lg transition-all hover:bg-blue-700 hover:shadow-xl"
          >
            Talk to Advisor
          </Link>
          <Link
            href="/explore"
            className="rounded-lg border border-gray-300 px-8 py-3 text-lg font-semibold transition-colors hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-900"
          >
            Browse Modules
          </Link>
        </div>
      </section>

      {/* Categories grid */}
      <section className="bg-gray-50 px-8 py-16 dark:bg-gray-900/50">
        <div className="mx-auto max-w-5xl">
          <h2 className="mb-8 text-center text-2xl font-bold">18 Categories, 86 Modules</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {CATEGORIES.map((cat) => (
              <div
                key={cat.name}
                className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900"
              >
                <span className="text-2xl">{cat.icon}</span>
                <div>
                  <p className="font-medium">{cat.name}</p>
                  <p className="text-sm text-gray-500">{cat.count} modules</p>
                </div>
              </div>
            ))}
          </div>
          <p className="mt-4 text-center text-sm text-gray-500">
            + more categories including Security, Deployment, Caching, and Orchestration
          </p>
        </div>
      </section>

      {/* Features */}
      <section className="px-8 py-16">
        <div className="mx-auto max-w-5xl">
          <h2 className="mb-8 text-center text-2xl font-bold">How It Works</h2>
          <div className="grid gap-8 md:grid-cols-2">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="rounded-lg border border-gray-200 p-6 dark:border-gray-800"
              >
                <h3 className="mb-2 text-lg font-semibold">{f.title}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-blue-600 px-8 py-16 text-center text-white">
        <h2 className="mb-4 text-3xl font-bold">Ready to build your AI stack?</h2>
        <p className="mb-8 text-blue-100">
          Start with the AI advisor or browse modules directly.
        </p>
        <Link
          href="/advisor"
          className="rounded-lg bg-white px-8 py-3 font-semibold text-blue-600 transition-colors hover:bg-blue-50"
        >
          Get Started Free
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 px-8 py-8 dark:border-gray-800">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <span className="text-sm text-gray-500">AI Tech Aggregator</span>
          <div className="flex gap-6 text-sm text-gray-500">
            <Link href="/explore" className="hover:text-gray-700 dark:hover:text-gray-300">Explore</Link>
            <Link href="/pricing" className="hover:text-gray-700 dark:hover:text-gray-300">Pricing</Link>
            <Link href="/advisor" className="hover:text-gray-700 dark:hover:text-gray-300">Advisor</Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
