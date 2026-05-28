"""Tests for impact-aware slot policy."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.schemas.constraint_state import ConstraintSource, ConstraintState
from src.services.slot_impact_policy import SlotImpactPolicy


@pytest.mark.asyncio
async def test_budget_is_impactful_when_missing(monkeypatch):
    policy = SlotImpactPolicy(db=MagicMock())
    mock_pipeline = MagicMock()
    mock_pipeline.module_service = MagicMock()
    mock_pipeline.module_service.list_modules = AsyncMock(
        return_value=(
            [
                SimpleNamespace(slug="qdrant", name="qdrant", tagline="", description="", pricing_model="open_source", comparison_scores={}, technical_specs={}, supported_operations=[]),
                SimpleNamespace(slug="pinecone", name="pinecone", tagline="", description="", pricing_model="paid", comparison_scores={}, technical_specs={}, supported_operations=[]),
            ],
            2,
        )
    )
    mock_pipeline.preview_signature = MagicMock(side_effect=["qdrant", "qdrant,pinecone", "qdrant"])

    def fake_get_pipeline(db, playbook_id, category=None):
        return mock_pipeline

    monkeypatch.setattr(
        "src.services.slot_impact_policy.get_pipeline",
        fake_get_pipeline,
    )

    state = ConstraintState()
    questions = {
        "budget": {"question": "Budget?", "options": []},
        "scale": {"question": "Scale?", "options": []},
        "deployment_preference": {"question": "Deploy?", "options": []},
    }
    q = await policy.next_impactful_question(
        "vector_db_comparison",
        state,
        ["budget", "scale", "deployment_preference"],
        questions,
    )
    assert q is not None
    assert q["id"] == "budget"
