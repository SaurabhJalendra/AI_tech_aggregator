'use client';

import { type ReactNode } from 'react';

interface AdvisorLayoutProps {
  children: ReactNode;
}

/**
 * AdvisorLayout provides the 30/70 split container for the advisor experience.
 * Left 30%: Chat panel (conversation with the AI advisor)
 * Right 70%: Main panel (dynamic content - diagrams, comparisons, code, etc.)
 */
export default function AdvisorLayout({ children }: AdvisorLayoutProps) {
  return (
    <div className="flex h-[calc(100vh-64px)] overflow-hidden">
      {children}
    </div>
  );
}
