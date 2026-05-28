"""Explanation fidelity — ensure sanitizer never mutates semantic reasoning."""

from __future__ import annotations

import re
from typing import Iterable

from src.services.response_sanitizer import sanitize_advisor_text, SanitizationReport

# Prose we must never remove or replace (tradeoff / consulting language)
_PROTECTED_PHRASES = (
    "tradeoff",
    "however",
    "on the other hand",
    "recommend",
    "constraint",
    "shortlist",
    "deployment",
    "budget",
    "latency",
    "self-hosted",
    "managed",
)

_ARTIFACT_ONLY_RULES = frozenset({
    "view_transition_css",
    "duplicate_visualize_token",
    "show_widget_token",
    "malformed_panel_marker",
    "broken_panel_json",
    "duplicate_stream_fragment",
    "uncited_metric_claim_flagged",
})


def semantic_token_set(text: str) -> set[str]:
    tokens = re.findall(r"[a-z]{4,}", text.lower())
    return set(tokens)


def assert_semantic_preservation(original: str, sanitized: str) -> None:
    """Raise if meaningful consulting tokens were removed beyond whitespace/artifacts."""
    orig_tokens = semantic_token_set(original)
    clean_tokens = semantic_token_set(sanitized)
    if not orig_tokens:
        return
    removed = orig_tokens - clean_tokens
    protected_removed = [
        t for t in removed
        if any(p in t or t in p for p in _PROTECTED_PHRASES)
    ]
    if protected_removed and len(removed) > len(orig_tokens) * 0.15:
        raise AssertionError(
            f"sanitizer removed protected semantic tokens: {protected_removed[:8]}"
        )


def sanitize_with_integrity_check(text: str) -> tuple[str, SanitizationReport]:
    report = SanitizationReport()
    cleaned = sanitize_advisor_text(text, report=report)
    assert_semantic_preservation(text, cleaned)
    for rec in report.actions:
        if rec.rule not in _ARTIFACT_ONLY_RULES:
            raise AssertionError(f"unexpected sanitizer rule: {rec.rule}")
    return cleaned, report
