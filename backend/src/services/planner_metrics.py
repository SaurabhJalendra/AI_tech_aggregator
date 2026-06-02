"""In-memory planner health counters (internal observability only)."""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Any

_lock = threading.Lock()
_counters: dict[str, int] = defaultdict(int)


def record_turn(telemetry: dict[str, Any]) -> None:
    with _lock:
        _counters["turns_total"] += 1
        mode = telemetry.get("planner_mode", "on")
        _counters[f"mode_{mode}"] += 1

        if telemetry.get("intercepted"):
            _counters["intercepted"] += 1
        if telemetry.get("llm_used"):
            _counters["llm_used"] += 1
        if telemetry.get("clarification_triggered"):
            _counters["clarification"] += 1
        if telemetry.get("fallback_reason"):
            _counters["fallback"] += 1
        shadow = telemetry.get("shadow_result") or {}
        if isinstance(shadow, dict) and shadow.get("routing_disagreement"):
            _counters["shadow_divergence"] += 1
        if telemetry.get("flat_constraints_rejected"):
            _counters["flat_constraints_rejected"] += 1

        stream = telemetry.get("stream_lifecycle") or {}
        if stream.get("timeout"):
            _counters["stream_timeout"] += 1
        if stream.get("disconnect"):
            _counters["stream_disconnect"] += 1
        if stream.get("adapter_timeout"):
            _counters["adapter_timeout"] += 1
        if stream.get("abnormal_termination"):
            _counters["stream_abnormal"] += 1

        payload = telemetry.get("payload_stats") or {}
        if isinstance(payload, dict):
            if payload.get("stripped_injection"):
                _counters["prompt_injection_stripped"] += 1
            if payload.get("flat_constraints_rejected"):
                _counters["flat_constraints_rejected"] += 1

        if telemetry.get("pipeline_used") == "filter_exhausted":
            _counters["negotiation_exhausted"] += 1
        elif telemetry.get("pipeline_used"):
            _counters["pipeline_success"] += 1

        turn_idx = telemetry.get("session_turn_index") or 0
        if turn_idx >= 20:
            _counters["long_session_turns"] += 1


def snapshot() -> dict[str, Any]:
    with _lock:
        turns = _counters["turns_total"] or 1
        return {
            "turns_total": _counters["turns_total"],
            "intercept_pct": round(100 * _counters["intercepted"] / turns, 2),
            "fallback_pct": round(100 * _counters["fallback"] / turns, 2),
            "clarification_pct": round(100 * _counters["clarification"] / turns, 2),
            "negotiation_exhausted_pct": round(100 * _counters["negotiation_exhausted"] / turns, 2),
            "shadow_divergence_pct": round(100 * _counters["shadow_divergence"] / turns, 2),
            "stream_timeout_pct": round(100 * _counters["stream_timeout"] / turns, 2),
            "stream_abnormal_pct": round(100 * _counters["stream_abnormal"] / turns, 2),
            "adapter_timeout_pct": round(100 * _counters["adapter_timeout"] / turns, 2),
            "flat_constraints_rejected_pct": round(
                100 * _counters["flat_constraints_rejected"] / turns, 2
            ),
            "prompt_injection_stripped_pct": round(
                100 * _counters["prompt_injection_stripped"] / turns, 2
            ),
            "long_session_turns": _counters["long_session_turns"],
            "raw": dict(_counters),
        }


def reset() -> None:
    with _lock:
        _counters.clear()
