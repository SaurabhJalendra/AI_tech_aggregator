"""Structured sanitization for advisor text before it reaches chat UI."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Known UI leak artifact types (structured, not free-form reasoning deletion)
_KNOWN_ARTIFACTS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("view_transition_css", re.compile(
        r"::view-transition-(?:group|old|new)\(\*\)\s*\{[^}]*\}", re.IGNORECASE
    )),
    ("duplicate_visualize_token", re.compile(r"\bV?visualizeV?visualize\b", re.IGNORECASE)),
    ("show_widget_token", re.compile(r"\bshow_widget\b", re.IGNORECASE)),
    ("malformed_panel_marker", re.compile(r"<!--\s*PANEL_CMD:(?!.*-->).*$", re.MULTILINE)),
    ("broken_panel_json", re.compile(r"<!--\s*PANEL_CMD:\s*\{[^}]*$", re.MULTILINE)),
)

_DUPLICATE_LINE_PATTERN = re.compile(r"^(.{20,80})\n\1\n", re.MULTILINE)


@dataclass
class SanitizationRecord:
    rule: str
    original_snippet: str
    sanitized_snippet: str


@dataclass
class SanitizationReport:
    actions: list[SanitizationRecord] = field(default_factory=list)

    def to_trace_events(self) -> list[dict[str, Any]]:
        return [
            {
                "rule": rec.rule,
                "original": rec.original_snippet[:240],
                "sanitized": rec.sanitized_snippet[:240],
            }
            for rec in self.actions
        ]


def _record(report: SanitizationReport | None, rule: str, original: str, sanitized: str) -> None:
    if report is None:
        return
    report.actions.append(
        SanitizationRecord(
            rule=rule,
            original_snippet=original,
            sanitized_snippet=sanitized,
        )
    )


def sanitize_advisor_text(text: str, *, report: SanitizationReport | None = None) -> str:
    """Remove known UI artifacts; flag unsupported metrics without deleting reasoning."""
    cleaned = text

    for rule_name, pattern in _KNOWN_ARTIFACTS:
        match = pattern.search(cleaned)
        if match:
            _record(report, rule_name, match.group(0), "")
            cleaned = pattern.sub("", cleaned)

    dup = _DUPLICATE_LINE_PATTERN.search(cleaned)
    if dup:
        _record(report, "duplicate_stream_fragment", dup.group(0), dup.group(1) + "\n")
        cleaned = _DUPLICATE_LINE_PATTERN.sub(r"\1\n", cleaned)

    # Flag uncited benchmark claims in trace only — do not rewrite reasoning prose
    metric_claim = re.search(
        r"\d+\s*(?:%|percent).{0,40}(?:benchmark|improve|faster|better)",
        cleaned,
        re.IGNORECASE,
    )
    if metric_claim and report is not None:
        _record(
            report,
            "uncited_metric_claim_flagged",
            metric_claim.group(0),
            "(flagged — verify against benchmarks)",
        )

    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    result = cleaned.strip(" ")

    if report is not None and report.actions:
        for rec in report.actions:
            logger.info(
                "advisor_text_sanitized rule=%s original=%r sanitized=%r",
                rec.rule,
                rec.original_snippet[:120],
                rec.sanitized_snippet[:120],
            )

    return result
