"""Tests for the comparison engine."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.comparison_engine import ComparisonEngine


def _make_module(slug, scores):
    m = MagicMock()
    m.slug = slug
    m.name = slug.replace("_", " ").title()
    m.comparison_scores = scores
    return m


@pytest.fixture
def modules():
    return {
        "pinecone": _make_module("pinecone", {
            "performance": {"score": 8, "justification": "Fast"},
            "scalability": {"score": 9, "justification": "Auto-scale"},
            "cost_efficiency": {"score": 5, "justification": "Expensive"},
            "ease_of_use": {"score": 8, "justification": "Good SDK"},
        }),
        "weaviate": _make_module("weaviate", {
            "performance": {"score": 7, "justification": "Good"},
            "scalability": {"score": 7, "justification": "Manual scaling"},
            "cost_efficiency": {"score": 8, "justification": "Open source"},
            "ease_of_use": {"score": 7, "justification": "GraphQL API"},
        }),
    }


@pytest.mark.asyncio
async def test_compare_two_modules(mock_db, modules):
    """Test basic comparison of two modules."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = list(modules.values())
    mock_db.execute = AsyncMock(return_value=mock_result)

    engine = ComparisonEngine(mock_db)
    result = await engine.compare(
        slugs=["pinecone", "weaviate"],
        dimensions=["performance", "scalability", "cost_efficiency", "ease_of_use"],
    )

    assert result.modules == ["pinecone", "weaviate"]
    assert len(result.dimensions) == 4
    assert "pinecone" in result.matrix
    assert "weaviate" in result.matrix
    assert result.matrix["pinecone"]["performance"].value == 8
    assert result.matrix["weaviate"]["cost_efficiency"].value == 8


@pytest.mark.asyncio
async def test_compare_with_weights(mock_db, modules):
    """Test that weighted comparison changes ranking."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = list(modules.values())
    mock_db.execute = AsyncMock(return_value=mock_result)

    engine = ComparisonEngine(mock_db)

    # With cost_efficiency weighted high, weaviate should rank first
    result = await engine.compare(
        slugs=["pinecone", "weaviate"],
        dimensions=["performance", "cost_efficiency"],
        weights={"cost_efficiency": 5.0, "performance": 1.0},
    )

    assert result.overall_ranking[0] == "weaviate"


@pytest.mark.asyncio
async def test_compare_missing_modules(mock_db):
    """Test error when modules are not found."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)

    engine = ComparisonEngine(mock_db)
    with pytest.raises(ValueError, match="Modules not found"):
        await engine.compare(slugs=["nonexistent_a", "nonexistent_b"])


@pytest.mark.asyncio
async def test_compare_generates_recommendation(mock_db, modules):
    """Test that recommendation text is generated."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = list(modules.values())
    mock_db.execute = AsyncMock(return_value=mock_result)

    engine = ComparisonEngine(mock_db)
    result = await engine.compare(
        slugs=["pinecone", "weaviate"],
        dimensions=["performance", "scalability"],
    )

    assert len(result.recommendation) > 0
    assert "Pinecone" in result.recommendation or "Weaviate" in result.recommendation


@pytest.mark.asyncio
async def test_compare_rankings_per_dimension(mock_db, modules):
    """Test per-dimension rankings are correct."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = list(modules.values())
    mock_db.execute = AsyncMock(return_value=mock_result)

    engine = ComparisonEngine(mock_db)
    result = await engine.compare(
        slugs=["pinecone", "weaviate"],
        dimensions=["performance", "cost_efficiency"],
    )

    # Pinecone has performance=8, weaviate=7
    assert result.rankings["performance"][0] == "pinecone"
    # Weaviate has cost_efficiency=8, pinecone=5
    assert result.rankings["cost_efficiency"][0] == "weaviate"
