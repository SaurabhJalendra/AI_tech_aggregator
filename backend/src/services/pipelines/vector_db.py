"""Vector database comparison pipeline (Phase-2)."""

from __future__ import annotations

import logging
from typing import Any

from src.advisor_registry.loader import get_vector_db_decision_metadata
from src.models.module import Module
from src.schemas.advisor_trace import AdvisorTrace, FilterRecord
from src.schemas.constraint_state import ConstraintState
from src.services.module_service import ModuleService
from src.services.pipelines.base import PipelineResult, RecommendationPipeline
from src.services.pipelines.runtime import sort_scored_records
from src.services.scoring import comparison_dimension_weights, score_with_metadata

logger = logging.getLogger(__name__)


class VectorDbRecommendationPipeline(RecommendationPipeline):
    playbook_id = "vector_db_comparison"

    def __init__(self, db):
        super().__init__(db)
        self.module_service = ModuleService(db)
        self.decision_meta = get_vector_db_decision_metadata()

    async def run(
        self,
        state: ConstraintState,
        *,
        trace: AdvisorTrace | None = None,
        finalist_limit: int = 4,
        **kwargs: Any,
    ) -> PipelineResult:
        trace = trace or AdvisorTrace(
            playbook_id=self.playbook_id,
            constraint_snapshot=state.slot_values(),
        )
        trace.log_step("retrieve: vector_databases category")
        modules, _ = await self.module_service.list_modules(
            category="vector_databases",
            per_page=200,
        )
        trace.retrieved = [m.slug for m in modules]
        trace.log_step(f"retrieve: {len(modules)} candidates")

        passed, filtered_out = self._filter(modules, state, trace)
        trace.filtered_out = filtered_out
        if not passed:
            trace.log_step("filter: no modules match hard constraints")
            logger.warning(
                "vector_db pipeline: all %d candidates filtered out; constraints=%s",
                len(modules),
                state.slot_values(),
            )
            return PipelineResult(
                shortlist=[],
                weights=comparison_dimension_weights(state),
                trace=trace,
                extra={
                    "filter_exhausted": True,
                    "message": (
                        "No vector databases match your hard constraints. "
                        "Relax budget, deployment, or persistence requirements to see finalists."
                    ),
                },
            )
        scored = [score_with_metadata(m, self.decision_meta.get(m.slug, {}), state) for m in passed]
        trace.scores = scored
        ordered = sort_scored_records(scored)
        limit = finalist_limit
        if state.get("budget") == "low":
            limit = min(limit, 3)
        shortlist = [r.slug for r in ordered[:limit]]
        trace.shortlist = shortlist
        trace.log_step(f"shortlist: {shortlist}")

        logger.info("vector_db pipeline shortlist=%s", shortlist)
        return PipelineResult(
            shortlist=shortlist,
            weights=comparison_dimension_weights(state),
            trace=trace,
        )

    def preview_shortlist(self, modules: list[Module], state: ConstraintState, *, finalist_limit: int = 4) -> list[str]:
        passed, _ = self._filter(modules, state, None)
        scored = [score_with_metadata(m, self.decision_meta.get(m.slug, {}), state) for m in passed]
        ordered = sort_scored_records(scored)
        limit = finalist_limit
        if state.get("budget") == "low":
            limit = min(limit, 3)
        return [r.slug for r in ordered[:limit]]

    def preview_signature(self, state: ConstraintState, **kwargs: Any) -> str:
        modules = kwargs.get("modules")
        if not modules:
            return ""
        limit = kwargs.get("finalist_limit", 4)
        return ",".join(self.preview_shortlist(modules, state, finalist_limit=limit))

    def _filter(
        self,
        modules: list[Module],
        state: ConstraintState,
        trace: AdvisorTrace | None,
    ) -> tuple[list[Module], list[FilterRecord]]:
        removed: list[FilterRecord] = []
        kept: list[Module] = []
        budget = state.get("budget")
        deployment = state.get("deployment_preference")
        persistence = state.get("persistence_required")

        for module in modules:
            meta = self.decision_meta.get(module.slug, {})
            reason = self._filter_reason(meta, budget, deployment, persistence)
            if reason:
                removed.append(FilterRecord(slug=module.slug, reason=reason))
            else:
                kept.append(module)
        return kept, removed

    @staticmethod
    def _filter_reason(meta, budget, deployment, persistence) -> str | None:
        slug_tier = meta.get("pricing_tier", "medium")
        deployments = meta.get("deployment") or []
        if budget == "low" and slug_tier == "high":
            return "budget=low excludes high pricing tier"
        if budget == "low" and meta.get("operational_complexity") == "high":
            return "budget=low excludes high operational complexity"
        if deployment == "self_hosted":
            if deployments == ["cloud"]:
                return "deployment=self_hosted requires on_prem or hybrid"
            if "on_prem" not in deployments and "hybrid" not in deployments:
                return "deployment=self_hosted not supported"
        if deployment == "managed" and deployments == ["on_prem"]:
            return "deployment=managed excludes on_prem-only"
        if persistence is True and meta.get("persistence") is False:
            return "persistence_required=true"
        return None
