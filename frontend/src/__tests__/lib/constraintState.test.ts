import { describe, it, expect } from 'vitest';
import {
  emptyConstraintState,
  getConstraintValue,
  mergeConstraintStates,
  mergeOptionAnswer,
  resolveOutgoingConstraintState,
} from '@/lib/constraintState';

describe('constraintState', () => {
  it('mergeOptionAnswer maps flat metadata to typed slots', () => {
    const state = mergeOptionAnswer(null, {
      question_id: 'budget',
      answer_id: 'low',
      answer_label: 'Low / startup',
      metadata: { budget: 'low' },
    }, 'vector_db_comparison');

    expect(state.playbook_id).toBe('vector_db_comparison');
    expect(state.slots.budget).toMatchObject({
      value: 'low',
      source: 'option_card',
      confidence: 1,
      raw_label: 'Low / startup',
    });
    expect(state.slots.budget.value).toBe('low');
    expect(getConstraintValue(state, 'budget')).toBe('low');
  });

  it('resolveOutgoingConstraintState prefers explicit constraint_state', () => {
    const explicit = emptyConstraintState('rag_pipeline_design');
    explicit.slots.scale = { value: 'enterprise', source: 'explicit', confidence: 1 };

    const resolved = resolveOutgoingConstraintState(
      null,
      { constraint_state: explicit },
      'rag_pipeline_design'
    );
    expect(resolved?.slots.scale.value).toBe('enterprise');
  });

  it('emptyConstraintState has version and empty slots', () => {
    const state = emptyConstraintState();
    expect(state.slots).toEqual({});
    expect(state.version).toBe('1');
  });

  it('mergeConstraintStates preserves prior slots on partial updates', () => {
    const prior = emptyConstraintState('vector_db_comparison');
    prior.slots.budget = { value: 'low', source: 'option_card', confidence: 1 };
    prior.slots.scale = { value: 'prototype', source: 'option_card', confidence: 1 };

    const incoming = emptyConstraintState('vector_db_comparison');
    incoming.slots.deployment_preference = {
      value: 'managed',
      source: 'option_card',
      confidence: 1,
    };

    const merged = mergeConstraintStates(prior, incoming);
    expect(merged.slots.budget.value).toBe('low');
    expect(merged.slots.scale.value).toBe('prototype');
    expect(merged.slots.deployment_preference.value).toBe('managed');
  });

  it('resolveOutgoingConstraintState keeps prior slots on free-text follow-up', () => {
    const prior = emptyConstraintState('rag_pipeline_design');
    prior.slots.budget = { value: 'low', source: 'option_card', confidence: 1 };

    const resolved = resolveOutgoingConstraintState(prior, undefined, 'rag_pipeline_design');
    expect(resolved?.slots.budget.value).toBe('low');
  });

  it('mergeOptionAnswer preserves falsy answer_id values', () => {
    const state = mergeOptionAnswer(null, {
      question_id: 'use_reranker',
      answer_id: false,
      answer_label: 'No reranker',
      metadata: { use_reranker: false },
    });
    expect(state.slots.use_reranker.value).toBe(false);
  });
});
