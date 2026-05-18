"""Sanitize advisor text before it reaches chat UI."""

import re


ARTIFACT_PATTERNS = [
    re.compile(r"::view-transition-(?:group|old|new)\(\*\)\s*\{[^}]*\}", re.IGNORECASE),
    re.compile(r"\bV?visualizeV?visualize\b", re.IGNORECASE),
    re.compile(r"\bshow_widget\b", re.IGNORECASE),
]

UNSUPPORTED_METRIC_PATTERN = re.compile(
    r"[^.!?\n]*(?:\d+\s*(?:-|–|to)\s*\d+\s*%|\d+\s*%)[^.!?\n]*(?:benchmark|improve|improvement|increase|decrease|better)[^.!?\n]*[.!?]?",
    re.IGNORECASE,
)


def sanitize_advisor_text(text: str) -> str:
    """Remove leaked UI artifacts and unsupported metric claims from advisor text."""
    cleaned = text
    for pattern in ARTIFACT_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    cleaned = UNSUPPORTED_METRIC_PATTERN.sub(
        " Use benchmark data before making a numeric improvement claim.",
        cleaned,
    )
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip(" ")
