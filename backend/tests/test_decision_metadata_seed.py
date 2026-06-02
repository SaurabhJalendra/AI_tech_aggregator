"""Tests for decision metadata merge at seed time."""

from src.services.decision_metadata import (
    apply_decision_metadata_to_module,
    decision_from_comparison_dimensions,
    merge_overlay_into_technical_specs,
)
from types import SimpleNamespace


def test_merge_overlay_for_vector_db_slug():
    spec = {
        "meta": {"slug": "qdrant", "category": "vector_databases"},
        "technical_specs": {},
        "comparison_dimensions": {
            "performance": {"score": 9, "justification": "fast"},
        },
    }
    technical = merge_overlay_into_technical_specs(spec)
    assert "decision" in technical
    assert technical["decision"].get("pricing_tier") == "low"
    assert technical["decision"].get("deployment")


def test_fallback_decision_from_comparison_dimensions():
    derived = decision_from_comparison_dimensions(
        {"cost_efficiency": {"score": 8, "justification": "cheap"}}
    )
    assert derived["comparison_scores"]["cost_efficiency"] == 8
    assert derived["source"] == "module_spec"


def test_apply_decision_metadata_updates_unchanged_module_row():
    module = SimpleNamespace(slug="qdrant", technical_specs={})
    spec = {"meta": {"slug": "qdrant"}, "technical_specs": {}, "comparison_dimensions": {}}
    changed = apply_decision_metadata_to_module(module, spec)
    assert changed is True
    assert module.technical_specs["decision"]["pricing_tier"] == "low"

    changed_again = apply_decision_metadata_to_module(module, spec)
    assert changed_again is False
