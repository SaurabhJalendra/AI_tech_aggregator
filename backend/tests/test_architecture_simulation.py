"""Tests for Phase-4 architecture scenario simulation."""

from src.schemas.constraint_state import ConstraintSource, ConstraintState
from src.services.architecture_simulation import (
    apply_simulation_to_state,
    detect_architecture_simulation,
)


def test_detect_self_hosted_simulation():
    spec = detect_architecture_simulation(
        "What if we move to self-hosted deployment for this stack?"
    )
    assert spec is not None
    assert spec.slot_updates.get("deployment_preference") == "self_hosted"


def test_detect_latency_simulation():
    spec = detect_architecture_simulation("What if latency becomes critical for our SLA?")
    assert spec is not None
    assert spec.slot_updates.get("latency_priority") == "critical"


def test_apply_simulation_updates_state():
    state = ConstraintState()
    state.set_slot("scale", "prototype", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    spec = detect_architecture_simulation("What if we move to enterprise scale?")
    assert spec is not None
    trial = apply_simulation_to_state(state, spec)
    assert trial.get("scale") == "enterprise"
