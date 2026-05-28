"""Impact-aware missing-slot policy (Phase-2, all migrated playbooks)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.advisor_playbooks.loader import get_playbook, playbook_slot_impact_values
from src.schemas.constraint_state import ConstraintSource, ConstraintState
from src.services.pipeline_registry import get_pipeline


class SlotImpactPolicy:
    """Ask only when a slot materially changes pipeline output signature."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def next_impactful_question(
        self,
        playbook_id: str,
        state: ConstraintState,
        required_slots: list[str],
        question_catalog: dict[str, dict],
        *,
        category: str | None = None,
    ) -> dict | None:
        for slot_id in required_slots:
            if state.has(slot_id):
                continue
            q = question_catalog.get(slot_id)
            if not q:
                continue
            if await self._slot_impacts_output(playbook_id, state, slot_id, category=category):
                return {"id": slot_id, **q}
        return None

    async def _slot_impacts_output(
        self,
        playbook_id: str,
        state: ConstraintState,
        slot_id: str,
        *,
        category: str | None = None,
    ) -> bool:
        slot_values = self._slot_values_for_playbook(playbook_id)
        if slot_id not in slot_values:
            return True

        pipeline = get_pipeline(self.db, playbook_id, category=category)
        if pipeline is None:
            return True

        kwargs = await self._preview_kwargs(playbook_id, category)
        signatures: set[str] = set()
        for value in slot_values[slot_id]:
            trial = state.model_copy(deep=True)
            trial.set_slot(slot_id, value, source=ConstraintSource.DEFAULT, confidence=1.0, force=True)
            signatures.add(pipeline.preview_signature(trial, **kwargs))
        return len(signatures) > 1

    async def _preview_kwargs(self, playbook_id: str, category: str | None) -> dict:
        if playbook_id == "vector_db_comparison":
            modules, _ = await get_pipeline(self.db, playbook_id).module_service.list_modules(  # type: ignore[union-attr]
                category="vector_databases",
                per_page=200,
            )
            return {"modules": modules, "finalist_limit": 4}
        if playbook_id == "rag_pipeline_design":
            from src.advisor_playbooks.loader import get_playbook

            cats = (get_playbook("rag_pipeline_design") or {}).get("retrieval_config", {}).get(
                "pipeline_categories",
                [],
            )
            svc = get_pipeline(self.db, playbook_id).module_service  # type: ignore[union-attr]
            by_cat = {}
            for cat in cats:
                mods, _ = await svc.list_modules(category=cat, per_page=100)
                by_cat[cat] = mods
            return {"modules_by_cat": by_cat}
        if category:
            modules, _ = await get_pipeline(self.db, playbook_id, category=category).module_service.list_modules(  # type: ignore[union-attr]
                category=category,
                per_page=200,
            )
            return {"modules": modules, "finalist_limit": 4}
        return {}

    @staticmethod
    def _slot_values_for_playbook(playbook_id: str) -> dict[str, list[str]]:
        values = playbook_slot_impact_values(playbook_id)
        if values:
            return values
        if playbook_id.startswith("category_"):
            return playbook_slot_impact_values("vector_db_comparison")
        return {}
