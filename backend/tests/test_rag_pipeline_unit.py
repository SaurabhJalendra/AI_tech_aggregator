"""RAG pipeline unit checks without full ORM import (runs when pgvector absent)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.schemas.constraint_state import ConstraintSource, ConstraintState

pgvector = pytest.importorskip("pgvector", reason="pgvector required for RagPipelineDesignPipeline")

from src.services.pipelines.rag_design import RagPipelineDesignPipeline  # noqa: E402


def _mod(slug: str, cat: str):
    return SimpleNamespace(
        slug=slug,
        name=slug,
        tagline="",
        description="python",
        pricing_model="open_source",
        comparison_scores={},
        technical_specs={},
        supported_operations=[],
        pipeline_position=None,
        category=SimpleNamespace(slug=cat),
    )


@pytest.mark.asyncio
async def test_rag_pipeline_produces_stack_selections():
    pipeline = RagPipelineDesignPipeline(db=MagicMock())
    pipeline.module_service = MagicMock()

    async def list_side_effect(*, category: str, per_page: int = 100):
        if category == "vector_databases":
            return ([_mod("qdrant", category), _mod("pinecone", category)], 2)
        if category == "embeddings":
            return ([_mod("openai_embeddings", category)], 1)
        return ([_mod(f"{category}_mod", category)], 1)

    pipeline.module_service.list_modules = AsyncMock(side_effect=list_side_effect)

    with patch(
        "src.services.pipelines.rag_design.get_module_decision_metadata",
        return_value={},
    ):
        state = ConstraintState()
        state.set_slot("budget", "low", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
        state.set_slot("scale", "prototype", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
        state.set_slot(
            "implementation_preference",
            "python",
            source=ConstraintSource.EXPLICIT,
            confidence=1.0,
            force=True,
        )

        result = await pipeline.run(state)
        assert result.shortlist
        assert result.extra and result.extra.get("nodes")
        assert result.extra.get("stage_decisions")
        assert "pinecone" not in result.shortlist
