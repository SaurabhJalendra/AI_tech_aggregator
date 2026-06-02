'use client';

import Link from 'next/link';
import { useState } from 'react';
import ThemeToggle from '@/components/shared/ThemeToggle';

/**
 * Header is the top navigation bar used across the dashboard layout.
 */
export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="border-b border-[var(--border-subtle)] bg-[var(--surface-panel)]">
      <div className="flex h-16 items-center justify-between px-6">
        <div className="flex items-center gap-8">
          <Link href="/" className="text-lg font-bold">
            AI Tech Aggregator
          </Link>
          <nav className="hidden items-center gap-6 md:flex">
            <Link
              href="/advisor"
              className="text-sm text-[var(--text-secondary)] hover:text-[var(--foreground)]"
            >
              Advisor
            </Link>
            <Link
              href="/explore"
              className="text-sm text-[var(--text-secondary)] hover:text-[var(--foreground)]"
            >
              Explore
            </Link>
            <Link
              href="/dashboard"
              className="text-sm text-[var(--text-secondary)] hover:text-[var(--foreground)]"
            >
              Dashboard
            </Link>
            <Link
              href="/history"
              className="text-sm text-[var(--text-secondary)] hover:text-[var(--foreground)]"
            >
              History
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-4">
          <ThemeToggle />
          <Link
            href="/pricing"
            className="hidden text-sm text-[var(--text-secondary)] hover:text-[var(--foreground)] md:block"
          >
            Pricing
          </Link>
          {/* TODO: User avatar / sign in button */}
          <div className="hidden h-8 w-8 rounded-full bg-gray-200 md:block dark:bg-gray-700" />

          {/* Mobile hamburger button */}
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-md p-2 text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--foreground)] md:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? (
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <nav className="border-t border-[var(--border-subtle)] px-6 py-4 md:hidden">
          <div className="flex flex-col gap-3">
            <Link
              href="/advisor"
              className="text-sm text-[var(--text-secondary)] hover:text-[var(--foreground)]"
              onClick={() => setMobileMenuOpen(false)}
            >
              Advisor
            </Link>
            <Link
              href="/explore"
              className="text-sm text-[var(--text-secondary)] hover:text-[var(--foreground)]"
              onClick={() => setMobileMenuOpen(false)}
            >
              Explore
            </Link>
            <Link
              href="/dashboard"
              className="text-sm text-[var(--text-secondary)] hover:text-[var(--foreground)]"
              onClick={() => setMobileMenuOpen(false)}
            >
              Dashboard
            </Link>
            <Link
              href="/history"
              className="text-sm text-[var(--text-secondary)] hover:text-[var(--foreground)]"
              onClick={() => setMobileMenuOpen(false)}
            >
              History
            </Link>
            <Link
              href="/pricing"
              className="text-sm text-[var(--text-secondary)] hover:text-[var(--foreground)]"
              onClick={() => setMobileMenuOpen(false)}
            >
              Pricing
            </Link>
          </div>
        </nav>
      )}
    </header>
  );
}
