import { formatEntityLabel } from '@/lib/entityDisplay';

/** Human-readable consulting copy from pipeline filter / explain reasons. */

const REASON_RULES: Array<{
  test: (reason: string) => boolean;
  format: (slug: string, reason: string) => string;
}> = [
  {
    test: (r) => r.includes('budget=low') && r.includes('pricing tier'),
    format: (slug) =>
      `Excluded ${formatEntityLabel(slug)} because your budget focus favors lower-cost options.`,
  },
  {
    test: (r) => r.includes('budget=low') && r.includes('operational complexity'),
    format: (slug) =>
      `Excluded ${formatEntityLabel(slug)} because it adds operational overhead for a lean budget.`,
  },
  {
    test: (r) =>
      r.includes('deployment=self_hosted') &&
      (r.includes('cloud') || r.includes('on_prem') || r.includes('on-prem')),
    format: (slug) =>
      `Excluded ${formatEntityLabel(slug)} because you need self-hosted or hybrid deployment, not cloud-only.`,
  },
  {
    test: (r) => r.includes('deployment=self_hosted') && r.includes('not supported'),
    format: (slug) =>
      `Excluded ${formatEntityLabel(slug)} because it does not support your self-hosted deployment preference.`,
  },
  {
    test: (r) => r.includes('persistence'),
    format: (slug) =>
      `Excluded ${formatEntityLabel(slug)} because it does not meet your persistence requirements.`,
  },
  {
    test: (r) => r.toLowerCase().includes('open_source') || r.includes('prefer_open_source'),
    format: (slug) =>
      `Excluded ${formatEntityLabel(slug)} because you prefer open-source options.`,
  },
  {
    test: (r) => r.toLowerCase().includes('managed'),
    format: (slug) =>
      `Excluded ${formatEntityLabel(slug)} because your workload benefits from managed scaling and operations.`,
  },
  {
    test: (r) => r.toLowerCase().includes('scalab'),
    format: (slug) =>
      `Excluded ${formatEntityLabel(slug)} because it does not match your scalability requirements.`,
  },
];

export function humanizeFilterReason(slug: string, reason: string): string {
  const trimmed = reason.trim();
  if (!trimmed) {
    return `Excluded ${formatEntityLabel(slug)} based on your stated constraints.`;
  }

  for (const rule of REASON_RULES) {
    if (rule.test(trimmed)) {
      return rule.format(slug, trimmed);
    }
  }

  if (trimmed.length < 120 && !trimmed.includes('=')) {
    return `${formatEntityLabel(slug)}: ${trimmed}`;
  }

  return `Excluded ${formatEntityLabel(slug)} — ${trimmed.replace(/_/g, ' ')}`;
}

export function humanizeAppliedFilter(slug: string, reason: string): string {
  const trimmed = reason.trim();
  if (!trimmed) {
    return `${formatEntityLabel(slug)} matched your constraints.`;
  }
  if (!trimmed.includes('=') && trimmed.length < 100) {
    return trimmed;
  }
  return `Prioritized ${formatEntityLabel(slug)} — ${trimmed.replace(/_/g, ' ')}`;
}
