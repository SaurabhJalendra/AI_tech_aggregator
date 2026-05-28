"""Shared deterministic scoring helpers for Phase-2 pipelines."""

from __future__ import annotations

from typing import Any

from src.models.module import Module
from src.schemas.advisor_trace import ScoreRecord
from src.schemas.constraint_state import ConstraintSource, ConstraintState
from src.services.decision_metadata import get_decision_metadata

_PRICING_RANK = {"low": 0, "medium": 1, "high": 2}
_COMPLEXITY_PENALTY = {"low": 0.0, "medium": 0.3, "high": 0.8}

SCORE_MIN = 1.0
SCORE_MAX = 10.0


def clamp_score(value: float) -> float:
    """Keep pipeline and breakdown values on the canonical 1–10 scale."""
    return round(max(SCORE_MIN, min(SCORE_MAX, float(value))), 4)


def breakdown_average(breakdown: dict[str, float]) -> float:
    """Pipeline total = simple mean of displayed breakdown metrics (1–10 each)."""
    if not breakdown:
        return 5.0
    return clamp_score(sum(breakdown.values()) / len(breakdown))


def score_with_metadata(
    module: Module,
    meta: dict[str, Any] | None,
    state: ConstraintState,
) -> ScoreRecord:
    """Score one module; all breakdown values and total stay on 1–10."""
    meta = meta if meta is not None else get_decision_metadata(module.slug, module)
    breakdown: dict[str, float] = {}
    budget = state.get("budget")
    deployment = state.get("deployment_preference")

    comp = module.comparison_scores or {}

    def dim(meta_key: str, comp_key: str, default: float = 5.0) -> float:
        if meta_key in meta:
            return clamp_score(meta[meta_key])
        raw = comp.get(comp_key, {})
        if isinstance(raw, dict) and "score" in raw:
            return clamp_score(raw["score"])
        return clamp_score(default)

    breakdown["latency"] = dim("latency_score", "performance")
    breakdown["scalability"] = dim("scalability_score", "scalability")
    breakdown["ease_of_use"] = dim("ease_of_use_score", "ease_of_use")

    tier = meta.get("pricing_tier")
    if not tier:
        pm = (module.pricing_model or "medium").lower()
        tier = "low" if pm in ("open_source", "free", "free_tier") else "medium"
    tier_rank = _PRICING_RANK.get(str(tier), 1)
    if budget == "low":
        breakdown["cost_fit"] = clamp_score(10.0 - tier_rank * 4)
    elif budget == "high":
        breakdown["cost_fit"] = clamp_score(6.0 + tier_rank)
    else:
        breakdown["cost_fit"] = clamp_score(7.0)

    complexity = meta.get("operational_complexity", "medium")
    breakdown["ops_fit"] = clamp_score(10.0 - _COMPLEXITY_PENALTY.get(str(complexity), 0.3) * 3)

    deployments = meta.get("deployment") or []
    if deployment == "self_hosted" and "on_prem" in deployments:
        breakdown["deployment_fit"] = 9.0
    elif deployment == "managed" and "cloud" in deployments:
        breakdown["deployment_fit"] = 9.0
    else:
        breakdown["deployment_fit"] = 6.0

    if state.get("python_sdk"):
        text = f"{module.name} {module.description or ''}".lower()
        if "python" in text:
            breakdown["sdk_fit"] = 8.0

    total = breakdown_average(breakdown)
    confidences = [
        float(slot.confidence)
        for slot in state.slots.values()
        if slot is not None
    ]
    confidence = sum(confidences) / len(confidences) if confidences else 0.75
    retrieval = clamp_score(breakdown.get("deployment_fit", 6.0))
    return ScoreRecord(
        slug=module.slug,
        score=total,
        breakdown=breakdown,
        confidence=round(confidence, 6),
        retrieval_score=round(retrieval, 6),
    )


def comparison_dimension_weights(state: ConstraintState) -> dict[str, float]:
    weights = {
        "performance": 1.3,
        "scalability": 1.4,
        "ease_of_use": 1.2,
        "cost_efficiency": 1.0,
        "community": 1.0,
        "maturity": 1.1,
        "flexibility": 1.0,
        "data_privacy": 1.0,
    }
    if state.get("budget") == "low":
        weights["cost_efficiency"] = 2.5
    if state.get("deployment_preference") == "self_hosted":
        weights["data_privacy"] = 2.4
    scale = state.get("scale")
    if scale in ("growing_application", "enterprise"):
        weights["scalability"] = 2.5
        weights["performance"] = 2.0
    priority = state.get("quality_priority")
    if priority in ("reasoning", "accuracy"):
        weights["performance"] = max(weights["performance"], 2.5)
    elif priority == "low_latency":
        weights["performance"] = max(weights["performance"], 2.8)
    if state.get("latency_priority") == "high":
        weights["performance"] = max(weights["performance"], 2.8)
    return weights


