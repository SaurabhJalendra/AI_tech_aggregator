"""Explanation fidelity — sanitizer must not mutate consulting reasoning."""

import pytest

from src.services.explanation_integrity import (
    assert_semantic_preservation,
    sanitize_with_integrity_check,
)
from src.services.response_sanitizer import sanitize_advisor_text, SanitizationReport


CONSULTING_REASONING = """
Given your budget constraint and self-hosted deployment preference, **Qdrant** leads the
shortlist because it balances latency and operational fit. However, Weaviate remains a
viable tradeoff if you need stronger managed-hybrid flexibility.
"""


def test_consulting_reasoning_unchanged_after_sanitize():
    report = SanitizationReport()
    cleaned = sanitize_advisor_text(CONSULTING_REASONING, report=report)
    assert_semantic_preservation(CONSULTING_REASONING, cleaned)
    assert "tradeoff" in cleaned.lower()
    assert "shortlist" in cleaned.lower()
    assert "Qdrant" in cleaned


def test_artifact_stripped_without_touching_reasoning():
    polluted = (
        CONSULTING_REASONING
        + "\n::view-transition-group(*) { animation-duration: 0.25s; }\n"
        + "VvisualizeVvisualize show_widget"
    )
    cleaned, report = sanitize_with_integrity_check(polluted)
    assert "::view-transition" not in cleaned
    assert "show_widget" not in cleaned
    assert "tradeoff" in cleaned.lower()


def test_uncited_metric_flagged_not_deleted():
    text = "This can improve answer quality by 20-30% in benchmarks for retrieval."
    report = SanitizationReport()
    cleaned = sanitize_advisor_text(text, report=report)
    assert "20-30%" in cleaned
    assert any(r.rule == "uncited_metric_claim_flagged" for r in report.actions)
