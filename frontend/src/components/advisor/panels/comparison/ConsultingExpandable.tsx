'use client';

import type { ReactNode } from 'react';

interface ConsultingExpandableProps {
  title: string;
  subtitle?: string;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
  step?: number;
  /** Secondary sections sit visually below the hero. */
  subdued?: boolean;
}

export default function ConsultingExpandable({
  title,
  subtitle,
  open,
  onToggle,
  children,
  step,
  subdued = false,
}: ConsultingExpandableProps) {
  return (
    <section
      className={`consulting-section transition-opacity duration-300 ${subdued && !open ? 'opacity-80' : ''}`}
    >
      <button
        type="button"
        onClick={onToggle}
        className={`flex w-full items-start justify-between gap-4 rounded-xl border px-5 py-4 text-left transition-all duration-200 ${
          open
            ? 'border-[var(--border-subtle)] bg-[var(--surface-panel)] shadow-[var(--shadow-soft)]'
            : 'border-transparent bg-transparent hover:border-[var(--border-subtle)] hover:bg-[var(--surface-panel)]/50'
        }`}
        aria-expanded={open}
      >
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2.5">
            {step != null && (
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-[var(--border-subtle)] text-[11px] font-medium text-[var(--text-muted)]">
                {step}
              </span>
            )}
            <span
              className={`font-semibold ${open ? 'text-[var(--foreground)]' : 'text-[var(--text-secondary)]'}`}
            >
              {title}
            </span>
          </div>
          {subtitle && (
            <p className="mt-1 pl-8 text-xs leading-relaxed text-[var(--text-muted)]">{subtitle}</p>
          )}
        </div>
        <svg
          className={`mt-1 h-5 w-5 shrink-0 text-[var(--text-muted)] transition-transform duration-300 ease-out ${
            open ? 'rotate-180' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <div
        className={`grid transition-all duration-300 ease-out ${
          open ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'
        }`}
      >
        <div className="overflow-hidden">
          <div className="consulting-section-body space-y-5 pb-2 pt-4">{children}</div>
        </div>
      </div>
    </section>
  );
}
