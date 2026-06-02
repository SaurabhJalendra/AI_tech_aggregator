"""Tests for Phase-3C architecture_consulting payload."""

from src.schemas.advisor_trace import AdvisorTrace, FilterRecord, ScoreRecord
from src.schemas.constraint_state import ConstraintSlot, ConstraintSource, ConstraintState
from src.services.architecture_consulting import (
    build_adaptation_message,
    build_architecture_consulting,
    build_architecture_evolution,
)


def _state(**slots) -> ConstraintState:
    return ConstraintState(
        slots={
            k: ConstraintSlot(value=v, source=ConstraintSource.EXPLICIT, confidence=1.0)
            for k, v in slots.items()
        }
    )


def test_build_architecture_consulting_with_stage_decisions():
    trace = AdvisorTrace(playbook_id="rag_pipeline_design")
    trace.scores.append(ScoreRecord(slug="qdrant", score=8.2, breakdown={}))
    trace.filtered_out.append(
        FilterRecord(slug="pinecone", reason="budget=low excludes high tier")
    )
    trace.log_step("score: vector_databases")

    state = _state(
        deployment_preference="self_hosted",
        budget="low",
        scale="growing_application",
        language="python",
    )

    consulting = build_architecture_consulting(
        trace=trace,
        state=state,
        playbook_id="rag_pipeline_design",
        selections={"vector_databases": "qdrant"},
        stage_decisions={
            "vector_databases": {
                "selected_slug": "qdrant",
                "selected_label": "Qdrant",
                "winner_score": 8.2,
                "runners_up": [{"slug": "weaviate", "label": "Weaviate", "score": 7.1}],
                "rejected_slugs": ["pinecone"],
            }
        },
    )

    assert consulting["comparative_priority_line"]
    assert consulting["confidence"]["headline"]
    assert "qdrant" in consulting["node_decisions"]
    decision = consulting["node_decisions"]["qdrant"]
    assert "Qdrant" in decision["selection_reason"]
    assert decision["rejected"] or decision["considered"]


def test_architecture_evolution_detects_replacements():
    prev = {
        "selections": {"vector_databases": "pinecone"},
        "nodes": [
            {
                "id": "vector_databases",
                "slug": "pinecone",
                "label": "Pinecone",
                "category": "vector_databases",
            }
        ],
    }
    current_nodes = [
        {
            "id": "vector_databases",
            "slug": "qdrant",
            "label": "Qdrant",
            "category": "vector_databases",
        }
    ]
    evolution = build_architecture_evolution(
        prev,
        current_nodes,
        {"vector_databases": "qdrant"},
        {"message": "updated"},
    )
    assert evolution is not None
    assert evolution["replacements"][0]["from_slug"] == "pinecone"
    assert evolution["replacements"][0]["to_slug"] == "qdrant"


def test_consulting_evolution_null_does_not_break_replacement_check():
    """evolution key may be present with value None when no prior blueprint exists."""
    consulting = build_architecture_consulting(
        trace=AdvisorTrace(playbook_id="rag_pipeline_design"),
        state=_state(budget="high", scale="growing_application"),
        playbook_id="rag_pipeline_design",
        previous_panel_data={"selections": {}, "nodes": []},
    )
    assert consulting.get("evolution") is None
    evolution = consulting.get("evolution") or {}
    assert evolution.get("replacements") is None


def test_adaptation_message_on_constraint_change():
    old = {
        "slots": {
            "deployment_preference": {
                "value": "managed",
                "source": "explicit",
                "confidence": 1.0,
            }
        }
    }
    state = _state(deployment_preference="self_hosted")
    adaptation = build_adaptation_message(old, state)
    assert adaptation is not None
    assert "deployment" in adaptation["message"].lower()
