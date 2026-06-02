"""Module code playbook — deterministic module resolution (Phase-2)."""

from __future__ import annotations

import re
from typing import Any

from src.schemas.advisor_trace import AdvisorTrace
from src.schemas.constraint_state import ConstraintState
from src.services.module_service import ModuleService
from src.services.pipelines.base import PipelineResult, RecommendationPipeline
from src.services.scoring import comparison_dimension_weights


class ModuleCodePipeline(RecommendationPipeline):
    playbook_id = "module_code"

    def __init__(self, db):
        super().__init__(db)
        self.module_service = ModuleService(db)

    async def run(
        self,
        state: ConstraintState,
        *,
        trace: AdvisorTrace | None = None,
        message: str = "",
        focus_slug: str | None = None,
        **kwargs: Any,
    ) -> PipelineResult:
        trace = trace or AdvisorTrace(
            playbook_id=self.playbook_id,
            constraint_snapshot=state.slot_values(),
        )
        trace.log_step("retrieve: resolve module slug for code")
        slug = focus_slug or await self._resolve_slug(message)
        trace.retrieved = [slug] if slug else []
        if not slug:
            trace.log_step("shortlist: empty — no slug match")
            return PipelineResult(shortlist=[], weights={}, trace=trace)

        module = await self.module_service.get_by_slug(slug)
        if not module:
            return PipelineResult(shortlist=[], weights={}, trace=trace)

        trace.shortlist = [slug]
        trace.log_step(f"shortlist: {slug}")
        return PipelineResult(
            shortlist=[slug],
            weights=comparison_dimension_weights(state),
            trace=trace,
            extra={"module": module},
        )

    def preview_signature(self, state: ConstraintState, **kwargs: Any) -> str:
        return kwargs.get("focus_slug") or ""

    async def _resolve_slug(self, message: str) -> str | None:
        modules, _ = await self.module_service.list_modules(per_page=200)
        lower = message.lower()
        for candidate in modules:
            if candidate.slug.replace("_", " ") in lower or candidate.name.lower() in lower:
                return candidate.slug
        tokens = re.findall(r"[a-z][a-z0-9_]{2,}", lower)
        for token in sorted(tokens, key=len, reverse=True):
            for candidate in modules:
                if token in candidate.slug or token in candidate.name.lower().replace(" ", "_"):
                    return candidate.slug
        return None
