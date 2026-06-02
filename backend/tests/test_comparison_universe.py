"""Tests for same-abstraction-layer comparison filtering."""

import pytest

from src.schemas.constraint_state import ConstraintState
from src.services.comparison_universe import (
    filter_modules_by_layer,
    get_layer_slugs,
    resolve_comparison_layer,
)


class _FakeModule:
    def __init__(self, slug: str):
        self.slug = slug


def test_retrieval_layer_keywords():
    assert resolve_comparison_layer("retrieval", "compare reranking models for production") == "reranker"
    assert resolve_comparison_layer("retrieval", "llamaindex vs haystack") == "orchestration_framework"
    assert resolve_comparison_layer("retrieval", "hyde query transformation") == "query_optimization_technique"
    assert resolve_comparison_layer("retrieval", "hybrid search for rag") == "retrieval_strategy"


def test_retrieval_default_layer():
    assert resolve_comparison_layer("retrieval", "help with retrieval") == "retrieval_strategy"


def test_filter_modules_by_layer_excludes_mixed_abstractions():
    modules = [
        _FakeModule("hybrid_search"),
        _FakeModule("llamaindex"),
        _FakeModule("reranking_models"),
        _FakeModule("query_transformation"),
    ]
    kept, removed = filter_modules_by_layer(modules, "retrieval", "orchestration_framework")
    assert [m.slug for m in kept] == ["llamaindex"]
    assert "hybrid_search" in removed
    assert "reranking_models" in removed


def test_orchestration_layer_has_two_comparable_modules():
    slugs = get_layer_slugs("retrieval", "orchestration_framework")
    assert slugs == frozenset({"llamaindex", "haystack"})


def test_resolve_from_constraint_state():
    state = ConstraintState()
    state.set_slot("comparison_layer", "reranker", source="explicit", confidence=1.0)
    assert resolve_comparison_layer("retrieval", "anything", state=state) == "reranker"


def test_llm_layer_defaults_to_foundation_model():
    assert resolve_comparison_layer("llm_layer", "compare llms for production") == "foundation_model"


def test_llm_layer_foundation_model_subcategory_count():
    """Catalog should expose a broad foundation_model set (scaffold + legacy entries)."""
    from pathlib import Path
    import yaml

    specs_dir = Path(__file__).resolve().parents[2] / "modules_registry" / "specs"
    slugs = []
    for path in specs_dir.glob("*.yaml"):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        meta = raw.get("meta") or {}
        if meta.get("category") == "llm_layer" and meta.get("subcategory") == "foundation_model":
            slugs.append(meta["slug"])
    assert len(slugs) >= 19
    assert "gpt4_1" in slugs
    assert "llama_3" in slugs
    assert "deepseek_coder" in slugs
    assert "openai" not in slugs


def test_llm_layer_foundation_model_excludes_cloud_api_duplicates():
    class _ModuleWithSub(_FakeModule):
        def __init__(self, slug: str, subcategory: str):
            super().__init__(slug)
            self.subcategory = subcategory

    modules = [
        _ModuleWithSub("gpt4", "foundation_model"),
        _ModuleWithSub("openai", "cloud_api"),
        _ModuleWithSub("gemini", "foundation_model"),
        _ModuleWithSub("google_gemini", "cloud_api"),
        _ModuleWithSub("claude", "foundation_model"),
        _ModuleWithSub("anthropic_claude", "cloud_api"),
        _ModuleWithSub("groq_inference", "inference_provider"),
    ]
    kept, removed = filter_modules_by_layer(modules, "llm_layer", "foundation_model")
    assert {m.slug for m in kept} == {"gpt4", "gemini", "claude"}
    assert "openai" in removed
    assert "google_gemini" in removed
    assert "anthropic_claude" in removed
    assert "groq_inference" in removed
