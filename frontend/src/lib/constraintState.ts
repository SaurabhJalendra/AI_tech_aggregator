import type {

  ClientContext,

  ConstraintSlot,

  ConstraintStatePayload,

} from '@/types/chat';



/** Empty canonical constraint memory. */

export function emptyConstraintState(

  playbookId?: string | null

): ConstraintStatePayload {

  return {

    slots: {},

    playbook_id: playbookId ?? null,

    version: '1',

  };

}



export function hasConstraintSlots(state: ConstraintStatePayload | null): boolean {

  return Boolean(state && Object.keys(state.slots).length > 0);

}



/** Read a slot value by key (typed access for UI). */

export function getConstraintValue(

  state: ConstraintStatePayload | null,

  key: string

): ConstraintSlot['value'] | undefined {

  return state?.slots[key]?.value;

}



function slotFromFlatValue(

  value: unknown,

  source: ConstraintSlot['source'] = 'option_card'

): ConstraintSlot {

  return {

    value: value as ConstraintSlot['value'],

    source,

    confidence: 1,

  };

}



/** Merge incoming slots into base without dropping prior answers. */

export function mergeConstraintStates(

  base: ConstraintStatePayload | null,

  incoming: ConstraintStatePayload,

  playbookId?: string | null

): ConstraintStatePayload {

  const next = base

    ? { ...base, slots: { ...base.slots } }

    : emptyConstraintState(playbookId ?? incoming.playbook_id);



  for (const [key, slot] of Object.entries(incoming.slots || {})) {

    next.slots[key] = slot;

  }

  if (incoming.playbook_id) {

    next.playbook_id = incoming.playbook_id;

  }

  return next;

}



/** Merge option-card answer into prior ConstraintState (canonical path). */

export function mergeOptionAnswer(

  prior: ConstraintStatePayload | null,

  optionAnswer: NonNullable<ClientContext['option_answer']>,

  playbookId?: string | null

): ConstraintStatePayload {

  const next = prior

    ? { ...prior, slots: { ...prior.slots } }

    : emptyConstraintState(playbookId);



  const metadata = optionAnswer.metadata;

  if (metadata && typeof metadata === 'object') {

    for (const [key, value] of Object.entries(metadata)) {

      if (value && typeof value === 'object' && 'value' in value) {

        next.slots[key] = value as ConstraintSlot;

      } else if (key in metadata) {

        // Preserve falsy answers (false, 0, '')

        next.slots[key] = slotFromFlatValue(value);

      }

    }

  }



  if (optionAnswer.question_id && optionAnswer.answer_id !== undefined && optionAnswer.answer_id !== null) {

    next.slots[optionAnswer.question_id] = {

      value: optionAnswer.answer_id,

      source: 'option_card',

      confidence: 1,

      raw_label: optionAnswer.answer_label,

    };

  }



  return next;

}



/**

 * Resolve ConstraintState for an outgoing turn from store + optional client context.

 * Never wipes prior slots on free-text follow-ups.

 */

export function resolveOutgoingConstraintState(

  prior: ConstraintStatePayload | null,

  clientContext: ClientContext | undefined,

  playbookId?: string | null

): ConstraintStatePayload | null {

  let state = prior ?? emptyConstraintState(playbookId);



  if (clientContext?.constraint_state) {

    state = mergeConstraintStates(state, clientContext.constraint_state, playbookId);

  }

  if (clientContext?.option_answer) {

    state = mergeOptionAnswer(state, clientContext.option_answer, playbookId);

  }



  return hasConstraintSlots(state) ? state : prior;

}


