"""Tests for canonical ConstraintState."""

from src.schemas.constraint_state import ConstraintSource, ConstraintState
from src.services.constraint_state_service import ConstraintStateService


def test_merge_option_card_overrides_inferred():
    state = ConstraintStateService.build(
        "compare vector databases",
        {
            "option_answer": {
                "question_id": "budget",
                "answer_id": "low",
                "metadata": {"budget": "low"},
            },
        },
        playbook_id="vector_db_comparison",
    )
    assert state.get("budget") == "low"
    assert state.slots["budget"].source == ConstraintSource.OPTION_CARD
    assert state.slots["budget"].confidence == 1.0


def test_explicit_inference_from_message():
    state = ConstraintStateService.build(
        "Need cheap semantic retrieval for self-hosted deployment",
        None,
        playbook_id="vector_db_comparison",
    )
    assert state.get("budget") == "low"
    assert state.get("deployment_preference") == "self_hosted"


def test_higher_precedence_explicit_over_accumulated():
    state = ConstraintState()
    state.set_slot("budget", "medium", source=ConstraintSource.ACCUMULATED, confidence=0.9)
    state.set_slot("budget", "low", source=ConstraintSource.OPTION_CARD, confidence=1.0, force=True)
    assert state.get("budget") == "low"
