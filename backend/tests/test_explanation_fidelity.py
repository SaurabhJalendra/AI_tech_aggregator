"""Explanation fidelity regression — explanations must match pipeline evidence."""

from src.services.explanation_fidelity import validate_explanation_against_trace


def test_valid_explanation_passes():
    explain = {
        "shortlist": ["qdrant", "chroma"],
        "scores": {"qdrant": 0.82, "chroma": 0.71},
        "constraints": {"budget": "low"},
        "applied_filters": [{"slug": "pinecone", "reason": "budget"}],
    }
    text = (
        "Given your low budget, **qdrant** leads the shortlist over **chroma**. "
        "Some managed options were filtered by budget."
    )
    violations = validate_explanation_against_trace(text, explain)
    assert violations == []


def test_shortlist_mismatch_detected():
    explain = {"shortlist": ["qdrant"], "scores": {}, "constraints": {}, "applied_filters": []}
    trace = {"shortlist": ["qdrant", "chroma"]}
    violations = validate_explanation_against_trace(
        "Top pick is qdrant and chroma.",
        explain,
        trace=trace,
    )
    assert any("shortlist mismatch" in v for v in violations)


def test_hallucinated_metric_detected():
    explain = {
        "shortlist": ["qdrant"],
        "scores": {"qdrant": 0.5},
        "constraints": {},
        "applied_filters": [],
    }
    violations = validate_explanation_against_trace(
        "qdrant gives 95% improvement guaranteed.",
        explain,
    )
    assert any("unsupported claim" in v for v in violations)
