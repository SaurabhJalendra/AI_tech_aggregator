'use client';

import { getArchCategoryStyle } from '@/lib/architectureColors';
import { buildNodeConsultingProfile } from '@/lib/architectureConsulting';
import { resolveNodeDecision } from '@/lib/architectureConsultingPayload';
import { formatEntityLabel } from '@/lib/entityDisplay';
import type { ReactNode } from 'react';
import type { ArchitectureConsultingPayload, ArchNode } from '@/types/chat';

interface NodeDetailsDrawerProps {
  node: ArchNode | null;
  consulting: ArchitectureConsultingPayload | null;
  onClose: () => void;
  onLearn: () => void;
  onSwap: () => void;
  onCode: () => void;
  disabled?: boolean;
}

function Section({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="border-b border-[var(--border-subtle)] py-4 last:border-0">
      <h4 className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[var(--text-muted)]">
        {title}
      </h4>
      <div className="mt-2 space-y-2 text-sm leading-relaxed text-[var(--text-secondary)]">
        {children}
      </div>
    </section>
  );
}

export default function NodeDetailsDrawer({
  node,
  consulting,
  onClose,
  onLearn,
  onSwap,
  onCode,
  disabled,
}: NodeDetailsDrawerProps) {
  if (!node) return null;

  const style = getArchCategoryStyle(node.category);
  const pipelineDecision = resolveNodeDecision(consulting, node);
  const profile = buildNodeConsultingProfile(node);
  const displayName = formatEntityLabel(node.slug ?? node.label);

  const whySelected = pipelineDecision?.selection_reason ?? profile.whySelected;
  const operational = pipelineDecision?.operational_implications ?? profile.operationalNote;
  const scaling = pipelineDecision?.scaling_implications ?? profile.scalingNote;
  const deployment = pipelineDecision?.deployment_implications ?? profile.deploymentFit;
  const workloadFit = pipelineDecision?.workload_fit ?? profile.deploymentFit;

  return (
    <aside
      className="blueprint-drawer flex w-[min(100%,420px)] shrink-0 flex-col border-l border-[var(--border-subtle)] bg-[var(--surface-panel)] shadow-[var(--shadow-elevated)]"
      aria-label="Architectural consulting details"
    >
      <div className="flex items-start justify-between gap-3 border-b border-[var(--border-subtle)] px-5 py-4">
        <div className="min-w-0">
          <p className="text-[11px] font-medium uppercase tracking-wide text-[var(--accent)]">
            {profile.stageLabel}
          </p>
          <h3 className="mt-1 text-xl font-semibold leading-tight text-[var(--foreground)]">
            {profile.consultingTitle}
          </h3>
          <p className="mt-1 text-sm text-[var(--text-muted)]">{displayName}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-1.5 text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--foreground)]"
          aria-label="Close details"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-hidden px-5">
        <Section title="Decision path">
          <p>{whySelected}</p>

          {pipelineDecision?.considered && pipelineDecision.considered.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium text-[var(--foreground)]">Also considered</p>
              <ul className="mt-1.5 space-y-1">
                {pipelineDecision.considered.map((alt) => (
                  <li
                    key={alt.slug}
                    className="rounded-md border border-[var(--border-subtle)] bg-[var(--surface-secondary)] px-2.5 py-1.5 text-xs"
                  >
                    <span className="font-medium text-[var(--foreground)]">{alt.label}</span>
                    {alt.score != null && (
                      <span className="ml-1 text-[var(--text-muted)]">
                        · score {alt.score.toFixed(1)}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {pipelineDecision?.rejected && pipelineDecision.rejected.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium text-[var(--foreground)]">Considered but ruled out</p>
              <ul className="mt-1.5 space-y-2">
                {pipelineDecision.rejected.map((alt) => (
                  <li key={alt.slug} className="text-xs leading-relaxed">
                    <span className="font-medium text-[var(--foreground)]">{alt.label}</span>
                    <span className="text-[var(--text-muted)]"> — {alt.reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {(pipelineDecision?.tradeoffs_accepted?.length
            ? pipelineDecision.tradeoffs_accepted
            : profile.tradeoffNote
              ? [profile.tradeoffNote]
              : []
          ).map((t) => (
            <p key={t} className="mt-2 rounded-md bg-[var(--surface-secondary)] px-2.5 py-2 text-xs">
              <span className="font-medium text-[var(--foreground)]">Tradeoff accepted · </span>
              {t}
            </p>
          ))}
        </Section>

        <Section title="Workload fit">
          <p>{workloadFit}</p>
        </Section>

        <Section title="Operational implications">
          <p>{operational}</p>
        </Section>

        <Section title="Deployment">
          <p>{deployment}</p>
        </Section>

        <Section title="Scaling">
          <p>{scaling}</p>
        </Section>

        {node.description && !pipelineDecision && (
          <Section title="Recommendation detail">
            <p>{node.description}</p>
          </Section>
        )}

        {node.category && (
          <div className="py-3">
            <span
              className="inline-block rounded-full px-2.5 py-0.5 text-[11px] font-medium"
              style={{
                backgroundColor: style.fill,
                color: style.text,
                border: `1px solid ${style.stroke}`,
              }}
            >
              {profile.roleLine}
            </span>
          </div>
        )}
      </div>

      <div className="space-y-2 border-t border-[var(--border-subtle)] p-4">
        <p className="px-1 text-[11px] text-[var(--text-muted)]">
          Reasoning is trace-backed from planner scoring and filters — not generated copy.
        </p>
        <button
          type="button"
          disabled={disabled}
          onClick={onLearn}
          className="w-full rounded-lg bg-[var(--accent)] px-4 py-2.5 text-sm font-medium text-[var(--accent-foreground)] transition hover:bg-[var(--accent-hover)] disabled:opacity-50"
        >
          Understand this choice
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={onSwap}
          className="w-full rounded-lg border border-[var(--border-subtle)] px-4 py-2.5 text-sm font-medium text-[var(--foreground)] transition hover:bg-[var(--surface-hover)] disabled:opacity-50"
        >
          Compare alternatives
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={onCode}
          className="w-full rounded-lg border border-[var(--border-subtle)] px-4 py-2.5 text-sm font-medium text-[var(--foreground)] transition hover:bg-[var(--surface-hover)] disabled:opacity-50"
        >
          Integration & code
        </button>
      </div>
    </aside>
  );
}
