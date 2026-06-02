"""Phase-6 strategic infrastructure intelligence tests."""

from src.schemas.advisor_trace import AdvisorTrace
from src.schemas.constraint_state import ConstraintSource, ConstraintState
from src.services.consulting_memory import pin_current_architecture
from src.services.phase6_intelligence import (
    apply_tradeoff_lever,
    build_organizational_intelligence,
    enrich_phase6,
    build_tradeoff_simulator,
)


def test_organizational_intelligence_self_hosted():
    state = ConstraintState()
    state.set_slot(
        "deployment_preference",
        "self_hosted",
        source=ConstraintSource.EXPLICIT,
        confidence=1.0,
        force=True,
    )
    state.set_slot("scale", "enterprise", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    org = build_organizational_intelligence(state)
    assert org["insights"]
    assert "operational" in org["insights"][0].lower()


def test_tradeoff_lever_application():
    state = ConstraintState()
    trial = apply_tradeoff_lever(state, "lower_cost")
    assert trial is not None
    assert trial.get("budget") == "low"


def test_pin_strategy_workspace():
    profile = pin_current_architecture(
        {},
        title="Managed RAG",
        panel_data={"selections": {"vector_databases": "pinecone"}, "nodes": []},
        constraint_snapshot={"slots": {}},
    )
    assert len(profile["strategy_workspace"]["pinned"]) == 1


def test_enrich_phase6_blocks():
    state = ConstraintState()
    trace = AdvisorTrace(playbook_id="rag_pipeline_design")
    consulting = enrich_phase6(
        {},
        state=state,
        trace=trace,
        selections={"vector_databases": "qdrant"},
        stress={"scaling_pressure": "moderate"},
    )
    assert consulting.get("organizational_intelligence")
    assert consulting.get("cost_evolution")
    assert len(build_tradeoff_simulator(state)) >= 5
