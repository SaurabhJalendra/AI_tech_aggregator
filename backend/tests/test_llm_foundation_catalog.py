"""LLM foundation_model catalog and pipeline integration."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.schemas.constraint_state import ConstraintSource, ConstraintState
from src.services.comparison_universe import filter_modules_by_layer
from src.services.pipelines.category_comparison import CategoryComparisonPipeline


def _fm(slug: str, pricing: str = "paid"):
    return SimpleNamespace(
        slug=slug,
        name=slug,
        tagline="",
        description="",
        pricing_model=pricing,
        comparison_scores={
            "performance": {"score": 8},
            "scalability": {"score": 8},
            "ease_of_use": {"score": 8},
            "cost_efficiency": {"score": 7},
            "community": {"score": 7},
            "maturity": {"score": 7},
            "flexibility": {"score": 7},
            "data_privacy": {"score": 7},
        },
        technical_specs={},
        supported_operations=[],
    )


@pytest.mark.asyncio
async def test_llm_category_pipeline_shortlists_four_foundation_models():
    modules = [
        _fm("gpt4_1", "paid"),
        _fm("claude_sonnet", "paid"),
        _fm("gemini_flash", "freemium"),
        _fm("llama_3", "open_source"),
        _fm("phi", "open_source"),
        _fm("deepseek_coder", "freemium"),
        _fm("openai", "paid"),
    ]
    for m in modules:
        m.subcategory = "foundation_model" if m.slug != "openai" else "cloud_api"

    kept, removed = filter_modules_by_layer(modules, "llm_layer", "foundation_model")
    assert "openai" in removed
    assert len(kept) == 6

    pipeline = CategoryComparisonPipeline(db=MagicMock(), category="llm_layer", playbook_id="category_llm_layer")
    pipeline.module_service = MagicMock()
    pipeline.module_service.list_modules = AsyncMock(return_value=(modules, len(modules)))

    state = ConstraintState()
    state.set_slot("budget", "medium", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    state.set_slot("scale", "growing_application", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)

    result = await pipeline.run(state, finalist_limit=4, comparison_layer="foundation_model")
    assert len(result.shortlist) == 4
    assert "openai" not in result.shortlist
    assert any(f.slug == "openai" for f in result.trace.filtered_out)
