"""Shared Phase-2 recommendation pipeline contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.advisor_trace import AdvisorTrace
from src.schemas.constraint_state import ConstraintState


@dataclass
class PipelineResult:
    shortlist: list[str]
    weights: dict[str, float]
    trace: AdvisorTrace
    extra: dict[str, Any] | None = None


def attach_pipeline_context(
    client_context: dict | None,
    result: PipelineResult,
    *,
    playbook_id: str,
) -> None:
    if client_context is None:
        return
    result.trace.playbook_id = playbook_id
    client_context["advisor_trace"] = result.trace.model_dump(mode="json")
    client_context["recommendation_explain"] = result.trace.to_explain_payload()
    if result.extra:
        client_context["pipeline_extra"] = result.extra


class RecommendationPipeline(ABC):
    """Retrieve → filter → score → shortlist (playbook-specific)."""

    playbook_id: str

    def __init__(self, db: AsyncSession):
        self.db = db

    @abstractmethod
    async def run(
        self,
        state: ConstraintState,
        *,
        trace: AdvisorTrace | None = None,
        **kwargs: Any,
    ) -> PipelineResult:
        ...

    @abstractmethod
    def preview_signature(self, state: ConstraintState, **kwargs: Any) -> str:
        """Compact signature for slot-impact simulation."""
