"""Resolve Phase-2 recommendation pipelines by playbook id."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.advisor_playbooks.loader import get_playbook
from src.services.pipelines.architecture_review import ArchitectureReviewPipeline
from src.services.pipelines.base import RecommendationPipeline
from src.services.pipelines.category_comparison import CategoryComparisonPipeline
from src.services.pipelines.local_ai_stack import LocalAiStackPipeline
from src.services.pipelines.module_code import ModuleCodePipeline
from src.services.pipelines.rag_design import RagPipelineDesignPipeline
from src.services.pipelines.vector_db import VectorDbRecommendationPipeline

_PHASE2_PLAYBOOKS = frozenset({
    "vector_db_comparison",
    "rag_pipeline_design",
    "module_code",
    "architecture_review",
    "local_ai_stack",
})


def is_phase2_playbook(playbook_id: str | None) -> bool:
    if not playbook_id:
        return False
    if playbook_id in _PHASE2_PLAYBOOKS:
        return True
    return playbook_id.startswith("category_")


def get_pipeline(
    db: AsyncSession,
    playbook_id: str,
    *,
    category: str | None = None,
) -> RecommendationPipeline | None:
    if playbook_id == "vector_db_comparison":
        return VectorDbRecommendationPipeline(db)
    if playbook_id == "rag_pipeline_design":
        return RagPipelineDesignPipeline(db)
    if playbook_id == "module_code":
        return ModuleCodePipeline(db)
    if playbook_id == "architecture_review":
        return ArchitectureReviewPipeline(db)
    if playbook_id == "local_ai_stack":
        return LocalAiStackPipeline(db)
    if category:
        pb = get_playbook(playbook_id) or {}
        if pb.get("phase2_pipeline") or playbook_id.startswith("category_"):
            return CategoryComparisonPipeline(db, category=category, playbook_id=playbook_id)
        # category_comparison playbooks use category slug as playbook_id via resolve
        return CategoryComparisonPipeline(
            db,
            category=category,
            playbook_id=playbook_id or f"category_{category}",
        )
    return None
