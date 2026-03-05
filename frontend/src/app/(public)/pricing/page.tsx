import Link from 'next/link';

const TIERS = [
  {
    name: 'Free',
    price: '$0',
    period: 'forever',
    description: 'Get started with the AI advisor',
    features: [
      '10 advisor conversations/month',
      'Browse all 54 modules',
      'Basic comparisons (2 modules)',
      'Community support',
    ],
    cta: 'Get Started',
    href: '/advisor',
    highlighted: false,
  },
  {
    name: 'Pro',
    price: '$29',
    period: '/month',
    description: 'For developers building AI applications',
    features: [
      'Unlimited advisor conversations',
      'Advanced comparisons (5+ modules)',
      'Architecture diagram export',
      'Starter code generation',
      'API access (1,000 calls/month)',
      'Conversation history',
      'Priority support',
    ],
    cta: 'Start Pro Trial',
    href: '/advisor',
    highlighted: true,
  },
  {
    name: 'Team',
    price: '$99',
    period: '/month',
    description: 'For teams evaluating AI infrastructure',
    features: [
      'Everything in Pro',
      'Up to 10 team members',
      'Shared conversation history',
      'Custom evaluation criteria',
      'API access (10,000 calls/month)',
      'Dedicated support',
    ],
    cta: 'Contact Sales',
    href: '/advisor',
    highlighted: false,
  },
  {
    name: 'API',
    price: 'Usage',
    period: 'based',
    description: 'Integrate the advisor into your tools',
    features: [
      'REST API access',
      'Python SDK',
      'CLI tool',
      'MCP Server integration',
      'Custom rate limits',
      'Webhook notifications',
      'SLA guarantee',
    ],
    cta: 'View API Docs',
    href: '/advisor',
    highlighted: false,
  },
];

export default function PricingPage() {
  return (
    <main className="min-h-screen p-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-12 text-center">
          <h1 className="mb-4 text-4xl font-bold">Simple, transparent pricing</h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Start free. Upgrade when you need more.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-4">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`flex flex-col rounded-xl p-6 ${
                tier.highlighted
                  ? 'border-2 border-blue-600 shadow-lg'
                  : 'border border-gray-200 dark:border-gray-800'
              }`}
            >
              {tier.highlighted && (
                <span className="mb-4 inline-block w-fit rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                  Most Popular
                </span>
              )}
              <h2 className="text-xl font-bold">{tier.name}</h2>
              <div className="mt-2">
                <span className="text-3xl font-bold">{tier.price}</span>
                <span className="text-gray-500">{tier.period}</span>
              </div>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {tier.description}
              </p>

              <ul className="mt-6 flex-1 space-y-3">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm">
                    <span className="mt-0.5 text-green-500">&#10003;</span>
                    <span className="text-gray-700 dark:text-gray-300">{feature}</span>
                  </li>
                ))}
              </ul>

              <Link
                href={tier.href}
                className={`mt-6 block rounded-lg px-4 py-2 text-center text-sm font-medium transition-colors ${
                  tier.highlighted
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'border border-gray-300 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800'
                }`}
              >
                {tier.cta}
              </Link>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center text-sm text-gray-500">
          All plans include access to all 54 modules and the knowledge base.
          <br />
          Need a custom plan?{' '}
          <Link href="/advisor" className="text-blue-600 hover:underline">
            Talk to us
          </Link>
        </div>
      </div>
    </main>
  );
}
