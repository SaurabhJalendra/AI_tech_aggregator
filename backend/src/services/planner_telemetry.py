"""Structured planner telemetry per chat turn."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PlannerTurnTelemetry:
    planner_mode: str = "on"
    intercepted: bool = False
    intent_id: str | None = None
    playbook_id: str | None = None
    routing_confidence: float | None = None
    clarification_triggered: bool = False
    fallback_reason: str | None = None
    pipeline_used: str | None = None
    constraint_snapshot: dict[str, Any] = field(default_factory=dict)
    deterministic_path: bool = False
    llm_used: bool = False
    shadow_result: dict[str, Any] | None = None
    divergence_reason: str | None = None
    stream_lifecycle: dict[str, Any] = field(default_factory=dict)
    sanitization_events: list[dict[str, Any]] = field(default_factory=list)
    flat_constraints_rejected: bool = False
    session_turn_index: int = 0
    payload_stats: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def summarize_planner_events(events: list[str] | None) -> dict[str, Any]:
    """Extract panels and text from planner SSE without exposing full payloads."""
    if not events:
        return {"event_count": 0, "panels": [], "text_length": 0}

    panels: list[str] = []
    text_len = 0
    for raw in events:
        if not raw.startswith("data: "):
            continue
        try:
            data = json.loads(raw[6:].strip())
        except json.JSONDecodeError:
            continue
        if data.get("type") == "panel_command":
            cmd = data.get("command") or {}
            panels.append(str(cmd.get("panel", "unknown")))
        elif data.get("type") == "text":
            text_len += len(data.get("content") or "")

    return {"event_count": len(events), "panels": panels, "text_length": text_len}


def compare_shadow_outcomes(
    planner_summary: dict[str, Any],
    llm_summary: dict[str, Any],
) -> dict[str, Any]:
    """Compare planner vs LLM path for shadow-mode analytics."""
    planner_panels = set(planner_summary.get("panels") or [])
    llm_panels = set(llm_summary.get("panels") or [])
    panel_divergence = sorted(planner_panels ^ llm_panels)

    ranking_divergence = planner_summary.get("shortlist") != llm_summary.get("shortlist")
    routing_disagreement = bool(panel_divergence) or ranking_divergence

    reasons: list[str] = []
    if panel_divergence:
        reasons.append(f"panel_mismatch:{','.join(panel_divergence)}")
    if ranking_divergence:
        reasons.append("shortlist_mismatch")
    if planner_summary.get("event_count", 0) == 0 and llm_summary.get("text_length", 0) > 0:
        reasons.append("planner_silent_llm_active")

    return {
        "routing_disagreement": routing_disagreement,
        "panel_divergence": panel_divergence,
        "ranking_divergence": ranking_divergence,
        "planner_panels": list(planner_panels),
        "llm_panels": list(llm_panels),
        "divergence_reason": ";".join(reasons) if reasons else None,
        "confidence_mismatch": planner_summary.get("routing_confidence") != llm_summary.get(
            "routing_confidence"
        ),
    }


def log_planner_telemetry(telemetry: PlannerTurnTelemetry, *, session_id: str | None = None) -> None:
    payload = telemetry.to_dict()
    if session_id:
        payload["session_id"] = session_id
    logger.info("planner_telemetry %s", json.dumps(payload, default=str, sort_keys=True))
