"""Tests for semantic intent routing and planner merge."""

import pytest

from src.schemas.intent import IntentResult
from src.services.recommendation_planner import RecommendationPlanner
from src.services.semantic_intent import _cosine_similarity


def test_cosine_similarity_parallel_unit_vectors():
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert abs(_cosine_similarity(a, b) - 1.0) < 1e-9

    c = [0.0, 1.0, 0.0]
    assert abs(_cosine_similarity(a, c)) < 1e-9


def test_merge_prefers_heuristic_rag_over_semantic_vector():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]
    ir = IntentResult(
        intent_id="category:vector_databases",
        confidence=0.9,
        margin=0.2,
        matched_evidence=[],
        inferred_parameters={"category": "vector_databases"},
    )
    task = planner.detect_task(
        "Build a RAG pipeline with chunking and embeddings",
        None,
        ir,
    )
    assert task is not None
    assert task["type"] == "rag_pipeline"


def test_semantic_binds_vector_intent_when_heuristic_returns_none():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]
    ir = IntentResult(
        intent_id="category:vector_databases",
        confidence=0.55,
        margin=0.1,
        matched_evidence=[],
        inferred_parameters={"category": "vector_databases"},
    )
    task = planner.detect_task(
        "Need ANN index for similarity search on dense vectors",
        None,
        ir,
    )
    assert task is not None
    assert task["type"] == "category_comparison"
    assert task["category"] == "vector_databases"
    assert task.get("playbook_id") == "vector_db_comparison"


def test_merge_overrides_wrong_category_when_semantic_strong():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]
    ir = IntentResult(
        intent_id="category:vector_databases",
        confidence=0.52,
        margin=0.08,
        matched_evidence=[],
        inferred_parameters={"category": "vector_databases"},
    )
    task = planner.detect_task(
        "Compare retrieval tools for hybrid search",
        None,
        ir,
    )
    assert task is not None
    assert task["type"] == "category_comparison"
    assert task["category"] == "vector_databases"


def test_unknown_intent_result_degrades_to_heuristic_only():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]
    ir = IntentResult(
        intent_id="unknown",
        confidence=0.0,
        margin=None,
        matched_evidence=[],
        inferred_parameters={},
    )
    task = planner.detect_task("Help me pick a vector database.", None, ir)
    assert task is not None
    assert task["category"] == "vector_databases"


def test_explicit_intent_resolves_designing_to_rag_pipeline():
    from src.services.semantic_intent import _explicit_intent_from_text

    assert _explicit_intent_from_text("Designing") == "rag_pipeline"
    assert _explicit_intent_from_text("designing an end to end") == "rag_pipeline"


def test_explicit_intent_resolves_module_code_request():
    from src.services.semantic_intent import _explicit_intent_from_text

    assert (
        _explicit_intent_from_text(
            "Show me integration code for LangChain Text Splitters"
        )
        == "module_code"
    )


def test_explicit_intent_resolves_rag_request_without_ambiguity():
    from src.services.semantic_intent import _explicit_intent_from_text

    assert (
        _explicit_intent_from_text("Help me build a RAG pipeline with code examples")
        == "rag_pipeline"
    )


@pytest.mark.asyncio
async def test_detect_resolves_clarification_follow_up():
    from src.services.semantic_intent import SemanticIntentDetector

    det = SemanticIntentDetector()
    result = await det.detect(
        "Designing",
        {
            "active_task": "Help me build a RAG pipeline with solid architecture",
            "awaiting_intent_clarification": True,
        },
    )
    assert result.intent_id == "rag_pipeline"
    assert result.needs_clarification is False


@pytest.mark.asyncio
async def test_semantic_detector_returns_unknown_when_embeddings_disabled(monkeypatch):
    from src.core import config
    from src.services import semantic_intent as si

    monkeypatch.setattr(config.settings, "embeddings_enabled", False)
    det = si.SemanticIntentDetector()
    res = await det.detect("Need semantic retrieval infra", None)
    assert res.intent_id == "unknown"
    assert res.confidence == 0.0
