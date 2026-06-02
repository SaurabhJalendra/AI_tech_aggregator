# ConstraintState — canonical memory contract

## Single source of truth

All advisor constraint memory flows through **`ConstraintState`** (`backend/src/schemas/constraint_state.py`).

The frontend sends:

```json
{
  "constraint_state": {
    "version": "1",
    "playbook_id": "vector_db_comparison",
    "slots": {
      "budget": {
        "value": "low",
        "source": "option_card",
        "confidence": 1,
        "raw_label": "Low / startup"
      }
    }
  }
}
```

## Rejected inputs

- **`constraints`** (flat dict) — rejected at `validate_client_context()` with `flat_constraints_rejected` telemetry.
- Raw **`advisor_trace`** from client — not in allowlist; only server-generated trace reaches prompts.

## Backend hydration

`ConstraintStateService.build()`:

1. Hydrates from `constraint_state` slots
2. Merges `option_answer` metadata via `merge_flat_slot_values()` (metadata only)
3. Infers missing slots from message text (never overwrites answered slots)

## Planner usage

- Slot presence: `state.has(slot_id)` — falsy values (`false`, `0`, `""`) count as answered
- Trace snapshots: `state.slot_values()` (export only, not input)
- Missing slots: `RecommendationPlanner.next_missing_question(task, state)`

## Frontend

- `frontend/src/lib/constraintState.ts` — merge on send/receive, never wipe on free text
- `chatStore` always sends accumulated `constraint_state` on each turn
