"""Generic category comparison pipeline (Phase-2)."""

from __future__ import annotations

import logging
from typing import Any

from src.advisor_registry.loader import get_category_decision_metadata
from src.models.module import Module
from src.schemas.advisor_trace import AdvisorTrace, FilterRecord
from src.schemas.constraint_state import ConstraintState
from src.services.module_service import ModuleService
from src.services.pipelines.base import PipelineResult, RecommendationPipeline
from src.services.pipelines.vector_db import VectorDbRecommendationPipeline
from src.services.comparison_universe import (
    apply_comparison_layer_to_state,
    filter_modules_by_layer,
    resolve_comparison_layer,
)
from src.services.pipelines.runtime import sort_scored_records
from src.services.scoring import comparison_dimension_weights, score_with_metadata

logger = logging.getLogger(__name__)


class CategoryComparisonPipeline(RecommendationPipeline):
    """Deterministic category comparison; delegates to vector DB specialist when applicable."""

    def __init__(self, db, *, category: str, playbook_id: str):
        super().__init__(db)
        self.category = category
        self.playbook_id = playbook_id
        self.module_service = ModuleService(db)
        self.decision_meta = get_category_decision_metadata()
        self._vector_specialist = VectorDbRecommendationPipeline(db)

    async def run(
        self,
        state: ConstraintState,
        *,
        trace: AdvisorTrace | None = None,
        finalist_limit: int = 4,
        **kwargs: Any,
    ) -> PipelineResult:
        if self.category == "vector_databases":
            return await self._vector_specialist.run(state, trace=trace, finalist_limit=finalist_limit)

        trace = trace or AdvisorTrace(
            playbook_id=self.playbook_id,
            constraint_snapshot=state.slot_values(),
        )
        trace.log_step(f"retrieve: {self.category}")
        modules, _ = await self.module_service.list_modules(category=self.category, per_page=200)
        trace.retrieved = [m.slug for m in modules]

        layer = kwargs.get("comparison_layer") or resolve_comparison_layer(
            self.category, "", state
        )
        layer_filtered: list[FilterRecord] = []
        if layer:
            apply_comparison_layer_to_state(state, self.category, layer)
            trace.log_step(f"comparison_layer: {layer}")
            layer_modules, layer_removed = filter_modules_by_layer(modules, self.category, layer)
            for slug in layer_removed:
                layer_filtered.append(
                    FilterRecord(
                        slug=slug,
                        reason=f"comparison_layer={layer} (mixed abstraction layer)",
                    )
                )
            modules = layer_modules

        passed, removed = self._filter_generic(modules, state)
        trace.filtered_out = layer_filtered + removed
        scored = [score_with_metadata(m, self.decision_meta.get(m.slug, {}), state) for m in passed]
        trace.scores = scored
        ordered = sort_scored_records(scored)
        shortlist = [r.slug for r in ordered[:finalist_limit]]
        trace.shortlist = shortlist
        trace.log_step(f"shortlist: {shortlist}")

        return PipelineResult(
            shortlist=shortlist,
            weights=comparison_dimension_weights(state),
            trace=trace,
        )

    def preview_signature(self, state: ConstraintState, **kwargs: Any) -> str:
        if self.category == "vector_databases":
            return self._vector_specialist.preview_signature(state, **kwargs)
        modules = kwargs.get("modules") or []
        limit = kwargs.get("finalist_limit", 4)
        passed, _ = self._filter_generic(modules, state)
        scored = [score_with_metadata(m, self.decision_meta.get(m.slug, {}), state) for m in passed]
        ordered = sort_scored_records(scored)
        return ",".join(r.slug for r in ordered[:limit])

    def preview_shortlist(self, modules: list[Module], state: ConstraintState, *, finalist_limit: int = 4) -> list[str]:
        sig = self.preview_signature(state, modules=modules, finalist_limit=finalist_limit)
        return [s for s in sig.split(",") if s]

    def _filter_generic(
        self,
        modules: list[Module],
        state: ConstraintState,
    ) -> tuple[list[Module], list[FilterRecord]]:
        removed: list[FilterRecord] = []
        kept: list[Module] = []
        budget = state.get("budget")
        for module in modules:
            meta = self.decision_meta.get(module.slug, {})
            tier = meta.get("pricing_tier")
            if not tier:
                pm = (module.pricing_model or "").lower()
                tier = "low" if pm in ("open_source", "free", "free_tier") else "medium"
            if budget == "low" and tier == "high":
                removed.append(FilterRecord(slug=module.slug, reason="budget=low"))
            else:
                kept.append(module)
        if not kept and modules:
            return modules, removed
        return kept, removed
