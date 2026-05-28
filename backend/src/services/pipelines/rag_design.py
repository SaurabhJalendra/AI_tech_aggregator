"""RAG pipeline design — per-stage retrieve/filter/score (Phase-2)."""

from __future__ import annotations

import logging
from typing import Any

from src.advisor_playbooks.loader import get_playbook
from src.advisor_registry.loader import get_category_decision_metadata, get_module_decision_metadata
from src.models.module import Module
from src.schemas.advisor_trace import AdvisorTrace, FilterRecord
from src.schemas.constraint_state import ConstraintState
from src.services.module_service import ModuleService
from src.services.pipelines.base import PipelineResult, RecommendationPipeline
from src.services.pipelines.runtime import sort_scored_records
from src.services.scoring import comparison_dimension_weights, score_with_metadata

logger = logging.getLogger(__name__)


class RagPipelineDesignPipeline(RecommendationPipeline):
    playbook_id = "rag_pipeline_design"

    def __init__(self, db):
        super().__init__(db)
        self.module_service = ModuleService(db)
        self.decision_meta = get_category_decision_metadata()

    async def run(
        self,
        state: ConstraintState,
        *,
        trace: AdvisorTrace | None = None,
        **kwargs: Any,
    ) -> PipelineResult:
        trace = trace or AdvisorTrace(
            playbook_id=self.playbook_id,
            constraint_snapshot=state.slot_values(),
        )
        playbook = get_playbook(self.playbook_id) or {}
        categories = (playbook.get("retrieval_config") or {}).get("pipeline_categories") or []

        selections: dict[str, str] = {}
        stage_decisions: dict[str, dict[str, Any]] = {}
        nodes: list[dict] = []
        all_retrieved: list[str] = []

        for category in categories:
            trace.log_step(f"retrieve: category={category}")
            modules, _ = await self.module_service.list_modules(category=category, per_page=100)
            slugs = [m.slug for m in modules]
            all_retrieved.extend(slugs)
            if not modules:
                continue

            passed, removed = self._filter_category(modules, state, category)
            for rec in removed:
                trace.filtered_out.append(rec)

            scored = [
                score_with_metadata(m, self.decision_meta.get(m.slug, {}), state) for m in passed
            ]
            trace.scores.extend(scored)
            if not scored:
                continue
            ranked = sort_scored_records(scored)
            winner = ranked[0]
            selections[category] = winner.slug
            module = next(m for m in passed if m.slug == winner.slug)
            runners_up = [
                {
                    "slug": r.slug,
                    "label": next((m.name for m in passed if m.slug == r.slug), r.slug),
                    "score": r.score,
                }
                for r in ranked[1:4]
            ]
            stage_decisions[category] = {
                "node_id": category,
                "selected_slug": winner.slug,
                "selected_label": module.name,
                "winner_score": winner.score,
                "runners_up": runners_up,
                "rejected_slugs": [r.slug for r in removed],
            }
            nodes.append({
                "id": category,
                "label": module.name,
                "slug": module.slug,
                "category": category,
                "description": (module.tagline or module.description or category)[:120],
            })

        trace.retrieved = list(dict.fromkeys(all_retrieved))
        trace.shortlist = list(selections.values())
        trace.log_step(f"rag stack selections: {selections}")

        edges = []
        for src, tgt in zip(categories, categories[1:], strict=False):
            if src in selections and tgt in selections:
                edges.append({"from": src, "to": tgt})

        logger.info("rag_pipeline_design selections=%s", selections)
        return PipelineResult(
            shortlist=trace.shortlist,
            weights=comparison_dimension_weights(state),
            trace=trace,
            extra={
                "nodes": nodes,
                "edges": edges,
                "selections": selections,
                "stage_decisions": stage_decisions,
            },
        )

    def preview_signature(self, state: ConstraintState, **kwargs: Any) -> str:
        modules_by_cat: dict[str, list[Module]] = kwargs.get("modules_by_cat") or {}
        playbook = get_playbook(self.playbook_id) or {}
        categories = (playbook.get("retrieval_config") or {}).get("pipeline_categories") or []
        parts: list[str] = []
        for category in categories:
            modules = modules_by_cat.get(category, [])
            if not modules:
                continue
            passed, _ = self._filter_category(modules, state, category)
            scored = [
                score_with_metadata(m, self.decision_meta.get(m.slug, {}), state) for m in passed
            ]
            if scored:
                winner = sort_scored_records(scored)[0]
                parts.append(f"{category}:{winner.slug}")
        return "|".join(parts)

    def _filter_category(
        self,
        modules: list[Module],
        state: ConstraintState,
        category: str,
    ) -> tuple[list[Module], list[FilterRecord]]:
        removed: list[FilterRecord] = []
        kept: list[Module] = []
        budget = state.get("budget")
        impl = state.get("implementation_preference")

        for module in modules:
            meta = get_module_decision_metadata(module.slug)
            reason = None
            if budget == "low" and meta.get("pricing_tier") == "high":
                reason = "budget=low excludes high tier"
            if impl == "python" and category == "embeddings":
                text = f"{module.name} {module.description or ''}".lower()
                if "python" not in text and meta.get("pricing_tier") != "low":
                    if "openai" in module.slug:
                        reason = reason or "python_sdk preference deprioritizes cloud-only API"
            if reason:
                removed.append(FilterRecord(slug=module.slug, reason=reason))
            else:
                kept.append(module)
        if not kept and modules:
            return modules, removed
        return kept, removed
