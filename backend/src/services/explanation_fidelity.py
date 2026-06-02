"""Validate LLM-facing explanation payloads against deterministic pipeline evidence."""

from __future__ import annotations

import re
from typing import Any


def validate_explanation_against_trace(
    text: str,
    explain: dict[str, Any],
    *,
    trace: dict[str, Any] | None = None,
) -> list[str]:
    """
    Return list of fidelity violations (empty = pass).
    Used in tests and optional runtime guards.
    """
    violations: list[str] = []
    if not explain:
        return ["missing recommendation_explain payload"]

    shortlist = explain.get("shortlist") or []
    scores = explain.get("scores") or {}
    constraints = explain.get("constraints") or {}
    applied = explain.get("applied_filters") or []

    if trace:
        trace_shortlist = trace.get("shortlist") or []
        if trace_shortlist and list(shortlist) != list(trace_shortlist):
            violations.append("shortlist mismatch between explain and trace")

    lower = text.lower()
    for slug in shortlist:
        if slug.replace("_", " ") not in lower and slug not in lower:
            violations.append(f"explanation omits shortlist candidate {slug}")

    for filt in applied:
        slug = filt.get("slug") if isinstance(filt, dict) else None
        if slug and slug not in shortlist and slug in lower:
            violations.append(f"explanation cites filtered-out slug {slug} as candidate")

    if constraints.get("budget") == "low":
        for slug, score in scores.items():
            if slug == "pinecone" and "pinecone" in lower and "filter" not in lower:
                violations.append("mentions pinecone without noting budget filter context")

    hallucination_patterns = [
        r"\b\d{2,3}%\s+improvement\b",
        r"\bguarantee[ds]?\b",
        r"\balways the best\b",
    ]
    for pat in hallucination_patterns:
        if re.search(pat, lower):
            violations.append(f"unsupported claim pattern: {pat}")

    return violations


def build_narration_system_addendum(explain: dict[str, Any]) -> str:
    """Prompt block enforcing narration-only behavior."""
    return (
        "\n\n## DETERMINISTIC EVIDENCE (MANDATORY)\n"
        "The recommendation engine has ALREADY decided. You must NOT rerank, add candidates, "
        "or contradict this evidence. Explain tradeoffs using ONLY these facts:\n"
        f"{explain}\n"
        "Reference constraints, filters, scores, and shortlist slugs explicitly. "
        "If evidence is insufficient, say what is missing — do not invent rankings.\n"
    )
