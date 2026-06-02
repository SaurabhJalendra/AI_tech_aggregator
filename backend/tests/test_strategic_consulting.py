"""Strategic consulting intelligence tests."""

from src.schemas.constraint_state import ConstraintState
from src.schemas.intent import IntentResult
from src.services.architecture_simulation import (
    detect_architecture_simulation,
    simulation_from_intent,
)
from src.services.consulting_memory import merge_profile_from_state
from src.services.strategic_consulting import (
    build_strategy_branches,
    detect_dual_strategy_request,
    detect_strategy_branch_from_message,
    enrich_architecture_consulting,
)
from src.schemas.advisor_trace import AdvisorTrace


def test_detect_strategy_branch_from_explore_message():
    assert detect_strategy_branch_from_message(
        "Explore the Cost-first infrastructure strategy for this architecture. "
        "Explain operational consequences and future tradeoffs."
    ) == "cost_first"
    assert detect_strategy_branch_from_message("Compare pinecone vs qdrant") is None


def test_detect_dual_strategy_managed_vs_self_hosted():
    spec = detect_dual_strategy_request("Compare managed vs self-hosted for our RAG stack")
    assert spec is not None
    assert "Managed" in spec.left_label or "Self" in spec.right_label


def test_semantic_simulation_from_intent():
    intent = IntentResult(
        intent_id="architecture_simulation:traffic",
        confidence=0.88,
        margin=0.2,
        matched_evidence=[],
        inferred_parameters={},
        needs_clarification=False,
        clarification_prompt=None,
        alternatives=[],
    )
    spec = simulation_from_intent(intent)
    assert spec is not None
    assert spec.slot_updates.get("scale") == "growing_application"


def test_detect_simulation_paraphrase_latency():
    intent = IntentResult(
        intent_id="architecture_simulation:latency",
        confidence=0.9,
        margin=0.3,
        matched_evidence=[],
        inferred_parameters={},
        needs_clarification=False,
        clarification_prompt=None,
        alternatives=[],
    )
    spec = detect_architecture_simulation(
        "Suppose retrieval latency becomes problematic under load",
        intent,
    )
    assert spec is not None


def test_merge_consulting_profile():
    state = ConstraintState()
    state.set_slot("deployment_preference", "managed", source="explicit", confidence=1.0)
    state.set_slot("budget", "low", source="explicit", confidence=1.0)
    profile = merge_profile_from_state({}, state)
    assert profile["slots"]["deployment_preference"]["value"] == "managed"
    assert profile.get("infrastructure_direction") == "managed"


def test_strategy_branches_and_forecasts():
    state = ConstraintState()
    state.set_slot("scale", "prototype", source="default", confidence=0.5)
    branches = build_strategy_branches(state)
    assert len(branches) == 4
    consulting = enrich_architecture_consulting(
        {},
        state=state,
        trace=AdvisorTrace(playbook_id="rag_pipeline_design"),
        selections={"vector_databases": "qdrant"},
    )
    assert consulting.get("strategy_branches")
    assert consulting.get("strategic_forecasts")
    assert consulting.get("operational_stress")
