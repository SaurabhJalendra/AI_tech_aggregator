"""Tests for Phase-2 vector DB recommendation pipeline."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.schemas.constraint_state import ConstraintSource, ConstraintState
from src.services.pipelines.vector_db import VectorDbRecommendationPipeline


def _module(slug: str, pricing_model: str = "open_source"):
    return SimpleNamespace(
        slug=slug,
        name=slug,
        tagline="",
        description="",
        pricing_model=pricing_model,
        comparison_scores={},
        technical_specs={},
        supported_operations=[],
    )


@pytest.mark.asyncio
async def test_pipeline_low_budget_excludes_pinecone():
    pipeline = VectorDbRecommendationPipeline(db=MagicMock())
    pipeline.module_service = MagicMock()
    pipeline.module_service.list_modules = AsyncMock(
        return_value=(
            [
                _module("qdrant"),
                _module("weaviate"),
                _module("chromadb"),
                _module("pinecone", "paid"),
                _module("milvus"),
            ],
            5,
        )
    )

    state = ConstraintState()
    state.set_slot("budget", "low", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    state.set_slot("scale", "growing_application", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    state.set_slot(
        "deployment_preference",
        "managed",
        source=ConstraintSource.EXPLICIT,
        confidence=1.0,
        force=True,
    )

    result = await pipeline.run(state, finalist_limit=4)
    assert "pinecone" not in result.shortlist
    assert "milvus" not in result.shortlist
    assert len(result.shortlist) >= 2
    assert any(f.slug == "pinecone" for f in result.trace.filtered_out)


@pytest.mark.asyncio
async def test_pipeline_self_hosted_excludes_cloud_only():
    pipeline = VectorDbRecommendationPipeline(db=MagicMock())
    pipeline.module_service = MagicMock()
    pipeline.module_service.list_modules = AsyncMock(
        return_value=([_module("qdrant"), _module("pinecone", "paid")], 2)
    )

    state = ConstraintState()
    state.set_slot("budget", "medium", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    state.set_slot("scale", "growing_application", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    state.set_slot(
        "deployment_preference",
        "self_hosted",
        source=ConstraintSource.EXPLICIT,
        confidence=1.0,
        force=True,
    )

    result = await pipeline.run(state)
    assert "pinecone" not in result.shortlist
    assert "qdrant" in result.shortlist


@pytest.mark.asyncio
async def test_pipeline_does_not_fallback_when_all_filtered():
    pipeline = VectorDbRecommendationPipeline(db=MagicMock())
    pipeline.module_service = MagicMock()
    pipeline.module_service.list_modules = AsyncMock(
        return_value=([_module("pinecone", "paid")], 1)
    )

    state = ConstraintState()
    state.set_slot("budget", "low", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    state.set_slot("scale", "prototype", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    state.set_slot(
        "deployment_preference",
        "self_hosted",
        source=ConstraintSource.EXPLICIT,
        confidence=1.0,
        force=True,
    )

    result = await pipeline.run(state)
    assert result.shortlist == []
    assert result.extra.get("filter_exhausted") is True
    assert "No vector databases match" in (result.extra.get("message") or "")


def test_shortlist_order_is_deterministic():
    pipeline = VectorDbRecommendationPipeline(db=MagicMock())
    modules = [_module("weaviate"), _module("qdrant"), _module("chromadb")]
    state = ConstraintState()
    state.set_slot("budget", "low", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    state.set_slot("scale", "prototype", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    state.set_slot(
        "deployment_preference",
        "managed",
        source=ConstraintSource.EXPLICIT,
        confidence=1.0,
        force=True,
    )
    a = pipeline.preview_shortlist(modules, state)
    b = pipeline.preview_shortlist(modules, state)
    assert a == b
