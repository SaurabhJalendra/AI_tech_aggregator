"""Pipeline scoring stays on canonical 1–10 scale."""

from types import SimpleNamespace

from src.schemas.constraint_state import ConstraintSource, ConstraintState
from src.services.scoring import (
    SCORE_MAX,
    SCORE_MIN,
    breakdown_average,
    clamp_score,
    score_with_metadata,
)


def _pinecone_module():
    return SimpleNamespace(
        slug="pinecone",
        name="Pinecone",
        tagline="",
        description="Python vector database",
        pricing_model="paid",
        comparison_scores={},
    )


def test_clamp_score_bounds():
    assert clamp_score(0) == SCORE_MIN
    assert clamp_score(16.2) == SCORE_MAX
    assert clamp_score(7.5) == 7.5


def test_enterprise_scale_does_not_inflate_breakdown():
    meta = {
        "scalability_score": 9,
        "latency_score": 9,
        "ease_of_use_score": 9,
        "pricing_tier": "high",
        "operational_complexity": "low",
        "deployment": ["cloud"],
    }
    state = ConstraintState()
    state.set_slot("scale", "enterprise", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    state.set_slot("budget", "high", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    state.set_slot(
        "deployment_preference",
        "managed",
        source=ConstraintSource.EXPLICIT,
        confidence=1.0,
        force=True,
    )

    record = score_with_metadata(_pinecone_module(), meta, state)

    assert record.breakdown["scalability"] == 9.0
    assert all(SCORE_MIN <= v <= SCORE_MAX for v in record.breakdown.values())
    assert record.score == breakdown_average(record.breakdown)
    assert record.score == 9.0


def test_pipeline_total_matches_simple_mean_for_shortlist_trace_values():
    """Regression: UI total must equal average of chips (pinecone enterprise trace)."""
    pinecone_breakdown = {
        "latency": 9,
        "scalability": 9,
        "ease_of_use": 9,
        "cost_fit": 8,
        "ops_fit": 10,
        "deployment_fit": 9,
    }
    assert breakdown_average(pinecone_breakdown) == 9.0

    turbopuffer_breakdown = {
        "latency": 9,
        "scalability": 8,
        "ease_of_use": 7,
        "cost_fit": 7,
        "ops_fit": 10,
        "deployment_fit": 9,
    }
    assert breakdown_average(turbopuffer_breakdown) == 8.3333

    qdrant_breakdown = {
        "latency": 9,
        "scalability": 8,
        "ease_of_use": 8,
        "cost_fit": 6,
        "ops_fit": 9.1,
        "deployment_fit": 9,
    }
    assert breakdown_average(qdrant_breakdown) == 8.1833


def test_high_latency_priority_keeps_latency_on_scale():
    meta = {
        "scalability_score": 8,
        "latency_score": 9,
        "ease_of_use_score": 7,
        "pricing_tier": "medium",
        "operational_complexity": "medium",
        "deployment": ["cloud"],
    }
    state = ConstraintState()
    state.set_slot("latency_priority", "high", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)

    record = score_with_metadata(_pinecone_module(), meta, state)
    assert record.breakdown["latency"] == 9.0
    assert record.score <= SCORE_MAX
