"""Long-session ConstraintState continuity (20+ turns)."""

from src.schemas.constraint_state import ConstraintSource, ConstraintState
from src.services.constraint_state_service import ConstraintStateService


def _answer_slot(state: ConstraintState, slot: str, value) -> ConstraintState:
    state.set_slot(slot, value, source=ConstraintSource.OPTION_CARD, confidence=1.0, force=True)
    return state


def test_twenty_turn_constraint_accumulation_no_reset():
    state = ConstraintState(playbook_id="vector_db_comparison")
    slots_sequence = [
        ("budget", "low"),
        ("scale", "growing_application"),
        ("deployment_preference", "managed"),
        ("persistence_required", True),
        ("open_source_only", False),
    ]

    for turn in range(20):
        slot_id = slots_sequence[turn % len(slots_sequence)][0]
        value = slots_sequence[turn % len(slots_sequence)][1]
        message = f"turn {turn} follow-up on infrastructure"
        state = _answer_slot(state, slot_id, value)
        rebuilt = ConstraintStateService.build(
            message,
            {"constraint_state": state.model_dump(mode="json")},
            playbook_id="vector_db_comparison",
        )
        for key in list(state.slots.keys()):
            assert rebuilt.has(key), f"lost slot {key} on turn {turn}"
        state = rebuilt

    assert state.get("budget") == "low"
    assert state.has("deployment_preference")
    assert len(state.slots) >= 3


def test_falsy_slot_persists_across_turns():
    state = ConstraintState()
    state.set_slot("use_reranker", False, source=ConstraintSource.OPTION_CARD, confidence=1.0, force=True)

    for _ in range(5):
        state = ConstraintStateService.build(
            "continue",
            {"constraint_state": state.model_dump(mode="json")},
        )

    assert state.get("use_reranker") is False
    assert state.has("use_reranker")
