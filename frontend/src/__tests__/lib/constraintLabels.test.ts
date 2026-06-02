import { describe, expect, it } from 'vitest';
import { constraintStateToChips } from '@/lib/constraintLabels';
import type { ConstraintStatePayload } from '@/types/chat';

describe('constraintStateToChips', () => {
  it('formats slots for visible chip bar', () => {
    const state: ConstraintStatePayload = {
      slots: {
        budget: { value: 'low', source: 'option_card', confidence: 1, raw_label: 'Low budget' },
        deployment_preference: {
          value: 'managed',
          source: 'inferred',
          confidence: 0.8,
        },
      },
      version: '1',
    };
    const chips = constraintStateToChips(state);
    expect(chips.length).toBeGreaterThanOrEqual(2);
    expect(chips.some((c) => c.label.includes('Low budget') || c.label.toLowerCase().includes('budget'))).toBe(
      true
    );
  });

  it('skips default-source slots', () => {
    const state: ConstraintStatePayload = {
      slots: {
        noise: { value: 'x', source: 'default', confidence: 0.5 },
      },
      version: '1',
    };
    expect(constraintStateToChips(state)).toHaveLength(0);
  });
});
