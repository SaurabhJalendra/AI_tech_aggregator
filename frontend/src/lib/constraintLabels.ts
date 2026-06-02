import type { ConstraintSlot, ConstraintStatePayload } from '@/types/chat';
import { formatEntityLabel } from '@/lib/entityDisplay';

const SLOT_DISPLAY: Record<string, string> = {
  budget: 'Budget',
  budget_tier: 'Budget',
  scale: 'Scale',
  deployment: 'Deployment',
  deployment_preference: 'Deployment',
  persistence_required: 'Persistence',
  language: 'Language',
  prefer_open_source: 'Open source',
  use_case: 'Use case',
  team_size: 'Team size',
  compliance: 'Compliance',
  data_sensitivity: 'Data sensitivity',
};

function formatSlotValue(key: string, slot: ConstraintSlot): string {
  if (slot.raw_label && typeof slot.value === 'string') {
    return slot.raw_label;
  }

  const v = slot.value;
  if (typeof v === 'boolean') {
    return v ? SLOT_DISPLAY[key] || key : '';
  }
  if (Array.isArray(v)) {
    return v.map((x) => formatEntityLabel(String(x))).join(', ');
  }

  const str = String(v).replace(/_/g, ' ');
  if (key === 'budget' || key === 'budget_tier') {
    return `${str} budget`;
  }
  if (key === 'deployment' || key === 'deployment_preference') {
    return `${str} deployment`;
  }
  return str;
}

export interface ConstraintChip {
  id: string;
  label: string;
}

/** Visible consulting memory chips from ConstraintState. */
export function constraintStateToChips(
  state: ConstraintStatePayload | null
): ConstraintChip[] {
  if (!state?.slots) return [];

  const chips: ConstraintChip[] = [];
  for (const [key, slot] of Object.entries(state.slots)) {
    if (slot.source === 'default') continue;
    const label = formatSlotValue(key, slot);
    if (!label) continue;
    const prefix = SLOT_DISPLAY[key];
    chips.push({
      id: key,
      label: prefix && !label.toLowerCase().includes(prefix.toLowerCase())
        ? `${prefix}: ${label}`
        : label,
    });
  }
  return chips;
}

/** Natural-language lead-in for hero / explainability (“Since you prefer…”). */
export function buildConstraintAcknowledgement(
  state: ConstraintStatePayload | null
): string | null {
  if (!state?.slots) return null;

  const parts: string[] = [];
  const deploy = state.slots.deployment_preference?.value ?? state.slots.deployment?.value;
  if (deploy === 'self_hosted' || deploy === 'on_prem') {
    parts.push('you prefer self-hosted deployment');
  } else if (deploy === 'managed' || deploy === 'cloud') {
    parts.push('you want a managed deployment model');
  }

  const budget = state.slots.budget?.value ?? state.slots.budget_tier?.value;
  if (budget === 'low') parts.push('cost efficiency is a priority');

  const lang = state.slots.language?.value;
  if (lang === 'python' || lang === 'Python') parts.push('your stack is Python-heavy');

  const scale = state.slots.scale?.value;
  if (scale === 'enterprise') parts.push('you are planning for enterprise scale');
  else if (scale === 'growing_application') parts.push('your workload will grow over time');

  if (state.slots.prefer_open_source?.value === true) {
    parts.push('open source matters to your team');
  }

  if (parts.length === 0) return null;
  if (parts.length === 1) return `Since ${parts[0]}, `;
  const last = parts.pop();
  return `Since ${parts.join(', ')} and ${last}, `;
}
