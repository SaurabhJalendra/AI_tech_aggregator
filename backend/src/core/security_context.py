"""Lightweight client-context abuse tracking (internal observability)."""

from __future__ import annotations

import threading
from collections import defaultdict

from src.schemas.payload_sanitizer import SanitizationStats

_lock = threading.Lock()
_injection_hits: dict[str, int] = defaultdict(int)
_oversized_payloads: dict[str, int] = defaultdict(int)
ABUSE_INJECTION_THRESHOLD = 8


def record_context_sanitization(
    stats: SanitizationStats,
    *,
    session_id: str | None = None,
) -> dict[str, bool | int]:
    """Track repeated injection / oversized payloads per session."""
    key = session_id or "anonymous"
    with _lock:
        if stats.stripped_injection:
            _injection_hits[key] += stats.stripped_injection
        if stats.truncated_strings or stats.array_trimmed:
            _oversized_payloads[key] += 1
        injection_count = _injection_hits[key]
    return {
        "injection_hits": injection_count,
        "abuse_suspected": injection_count >= ABUSE_INJECTION_THRESHOLD,
        "oversized_events": _oversized_payloads[key],
    }


def abuse_snapshot() -> dict[str, dict[str, int]]:
    with _lock:
        return {
            "injection_hits": dict(_injection_hits),
            "oversized_payloads": dict(_oversized_payloads),
        }
