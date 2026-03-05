'use client';

import Link from 'next/link';

/**
 * Header is the top navigation bar used across the dashboard layout.
 */
export default function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 px-6 dark:border-gray-800">
      <div className="flex items-center gap-8">
        <Link href="/" className="text-lg font-bold">
          AI Tech Aggregator
        </Link>
        <nav className="hidden items-center gap-6 md:flex">
          <Link
            href="/advisor"
            className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
          >
            Advisor
          </Link>
          <Link
            href="/explore"
            className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
          >
            Explore
          </Link>
          <Link
            href="/dashboard"
            className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
          >
            Dashboard
          </Link>
          <Link
            href="/history"
            className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
          >
            History
          </Link>
        </nav>
      </div>

      <div className="flex items-center gap-4">
        <Link
          href="/pricing"
          className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
        >
          Pricing
        </Link>
        {/* TODO: User avatar / sign in button */}
        <div className="h-8 w-8 rounded-full bg-gray-200 dark:bg-gray-700" />
      </div>
    </header>
  );
}
