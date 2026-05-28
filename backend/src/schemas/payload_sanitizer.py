"""Recursive sanitization for nested user-controlled payloads."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

MAX_NESTING_DEPTH = 8
MAX_ARRAY_LENGTH = 32
MAX_DICT_KEYS = 64
MAX_STRING_LENGTH = 2_000
MAX_TOTAL_CHARS = 16_000
MAX_PROMPT_TOKEN_BUDGET_CHARS = 8_000

_INJECTION_PATTERNS = (
    re.compile(r"<\s*/?\s*(?:system|assistant|user|instruction)\s*>", re.I),
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions?", re.I),
    re.compile(r"you\s+are\s+now\s+(?:a|an)\s+", re.I),
    re.compile(r"<!--\s*PANEL_CMD:", re.I),
    re.compile(r"\{\s*\"type\"\s*:\s*\"(?:panel_command|system)\"", re.I),
)


@dataclass
class SanitizationStats:
    truncated_strings: int = 0
    stripped_keys: int = 0
    stripped_injection: int = 0
    depth_capped: int = 0
    array_trimmed: int = 0
    total_chars: int = 0
    flat_constraints_rejected: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "truncated_strings": self.truncated_strings,
            "stripped_keys": self.stripped_keys,
            "stripped_injection": self.stripped_injection,
            "depth_capped": self.depth_capped,
            "array_trimmed": self.array_trimmed,
            "total_chars": self.total_chars,
            "flat_constraints_rejected": self.flat_constraints_rejected,
        }


def _strip_dangerous(text: str, stats: SanitizationStats) -> str:
    cleaned = text
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(cleaned):
            stats.stripped_injection += 1
            cleaned = pattern.sub("", cleaned)
    return cleaned


def _cap_string(value: str, stats: SanitizationStats) -> str:
    text = _strip_dangerous(str(value), stats)
    if len(text) > MAX_STRING_LENGTH:
        stats.truncated_strings += 1
        text = text[:MAX_STRING_LENGTH]
    stats.total_chars += len(text)
    return text


def sanitize_nested(
    value: Any,
    *,
    depth: int = 0,
    stats: SanitizationStats | None = None,
) -> Any:
    """Deeply sanitize nested JSON-like structures."""
    stats = stats or SanitizationStats()

    if stats.total_chars >= MAX_TOTAL_CHARS:
        return None

    if depth > MAX_NESTING_DEPTH:
        stats.depth_capped += 1
        return None

    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        return _cap_string(value, stats)

    if isinstance(value, list):
        if len(value) > MAX_ARRAY_LENGTH:
            stats.array_trimmed += 1
            value = value[:MAX_ARRAY_LENGTH]
        return [sanitize_nested(item, depth=depth + 1, stats=stats) for item in value]

    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for idx, (key, item) in enumerate(value.items()):
            if idx >= MAX_DICT_KEYS:
                stats.stripped_keys += 1
                break
            safe_key = _cap_string(str(key), stats)[:128]
            if not safe_key:
                continue
            out[safe_key] = sanitize_nested(item, depth=depth + 1, stats=stats)
        return out

    return _cap_string(str(value), stats)


def estimate_prompt_chars(payload: dict[str, Any]) -> int:
    """Rough character budget for prompt-boundary checks."""
    total = 0
    for value in payload.values():
        if isinstance(value, str):
            total += len(value)
        elif isinstance(value, (dict, list)):
            total += len(str(value)[:MAX_PROMPT_TOKEN_BUDGET_CHARS])
    return total
