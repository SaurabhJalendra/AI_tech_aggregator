"""Structured advisor trace for Phase-2 explainability."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


_INTERNAL_FILTER_MARKERS = (
    "comparison_layer=",
    "mixed abstraction layer",
)


def is_user_visible_filter(reason: str) -> bool:
    """Exclude catalog-layer separation from end-user explainability."""
    lower = reason.lower()
    return not any(marker in lower for marker in _INTERNAL_FILTER_MARKERS)


def user_visible_filters(records: list["FilterRecord"]) -> list["FilterRecord"]:
    return [r for r in records if is_user_visible_filter(r.reason)]


class FilterRecord(BaseModel):
    slug: str
    reason: str


class ScoreRecord(BaseModel):
    slug: str
    score: float
    breakdown: dict[str, float] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    retrieval_score: float = Field(default=0.0, ge=0.0)


class AdvisorTrace(BaseModel):
    playbook_id: str | None = None
    intent_id: str | None = None
    constraint_snapshot: dict[str, Any] = Field(default_factory=dict)
    retrieved: list[str] = Field(default_factory=list)
    filtered_out: list[FilterRecord] = Field(default_factory=list)
    scores: list[ScoreRecord] = Field(default_factory=list)
    shortlist: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    missing_slot_asked: str | None = None
    slot_impact_notes: dict[str, str] = Field(default_factory=dict)

    def log_step(self, message: str) -> None:
        self.steps.append(message)

    def to_explain_payload(self) -> dict[str, Any]:
        return {
            "playbook_id": self.playbook_id,
            "shortlist": self.shortlist,
            "scores": {r.slug: r.score for r in self.scores},
            "score_breakdowns": {r.slug: r.breakdown for r in self.scores},
            "applied_filters": [
                f.model_dump() for f in user_visible_filters(self.filtered_out)
            ],
            "constraints": self.constraint_snapshot,
            "retrieved_count": len(self.retrieved),
            "reasoning_steps": self.steps,
        }
