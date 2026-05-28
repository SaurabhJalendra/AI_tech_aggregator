"""Paraphrase regression — same intent, playbook, slots, and shortlist stability."""

from __future__ import annotations

import math
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.schemas.constraint_state import ConstraintState
from src.schemas.intent import IntentResult
from src.services.recommendation_planner import RecommendationPlanner
from src.services.semantic_intent import SemanticIntentDetector, _cosine_similarity
from tests.fixtures.paraphrase_fixtures import (
    load_paraphrase_groups,
    load_vector_db_shortlist_snapshot,
)


def _unit_vector(dim: int, index: int) -> list[float]:
    vec = [0.0] * dim
    vec[index % dim] = 1.0
    return vec


def _mock_embedding_router(dim: int = 32) -> dict[str, list[float]]:
    """Map paraphrase families to orthogonal unit vectors for deterministic CI."""
    groups = load_paraphrase_groups()
    routing: dict[str, list[float]] = {}
    for idx, group in enumerate(groups):
        vec = _unit_vector(dim, idx)
        for message in group.get("messages") or []:
            routing[message.strip().lower()] = vec
    return routing


@pytest.fixture
def paraphrase_groups():
    return load_paraphrase_groups()


@pytest.fixture
def embedding_router():
    return _mock_embedding_router()


@pytest.mark.parametrize("group", load_paraphrase_groups(), ids=lambda g: g["group_id"])
def test_paraphrase_groups_share_playbook_and_slots(group):
    """Planner task metadata is identical across paraphrases when intent is fixed."""
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]
    expected = group["expected"]
    intent_id = expected["intent_id"]
    ir = IntentResult(
        intent_id=intent_id,
        confidence=0.55,
        margin=0.12,
        matched_evidence=[],
        inferred_parameters=(
            {"category": expected["category"]} if intent_id.startswith("category:") else {}
        ),
    )

    tasks = [
        planner.detect_task(message, None, ir)
        for message in group["messages"]
    ]
    assert all(t is not None for t in tasks)
    playbook_ids = {t["playbook_id"] for t in tasks}
    assert len(playbook_ids) == 1
    assert playbook_ids.pop() == expected["playbook_id"]

    required_sets = {tuple(t["required_constraints"]) for t in tasks}
    assert len(required_sets) == 1

    first_slots = [
        (planner.next_missing_question(t, ConstraintState()) or {}).get("id")
        for t in tasks
    ]
    assert len(set(first_slots)) == 1
    assert first_slots[0] == expected.get("first_required_slot")


@pytest.mark.parametrize("group", load_paraphrase_groups(), ids=lambda g: g["group_id"])
@pytest.mark.asyncio
async def test_semantic_detect_same_intent_for_paraphrase_group(group):
    """Mocked embeddings route every paraphrase in a group to the same intent_id."""
    det = SemanticIntentDetector()
    expected_intent = group["expected"]["intent_id"]

    exemplars = det._exemplars
    intent_indices: dict[str, int] = {}
    vectors: list[list[float]] = []
    for ex in exemplars:
        iid = ex["intent_id"]
        if iid not in intent_indices:
            intent_indices[iid] = len(intent_indices)
        vectors.append(_unit_vector(32, intent_indices[iid]))

    target_vec = _unit_vector(32, intent_indices.get(expected_intent, 0))

    async def fake_embedding(text: str, *, for_query: bool = False):
        return target_vec

    with patch("src.services.semantic_intent.generate_embedding", side_effect=fake_embedding), patch(
        "src.services.semantic_intent.generate_embeddings_batch",
        return_value=vectors,
    ), patch("src.services.semantic_intent.settings") as mock_settings:
        mock_settings.semantic_intent_enabled = True
        mock_settings.embeddings_enabled = True
        mock_settings.semantic_intent_min_confidence = 0.32
        mock_settings.semantic_intent_clarify_low = 0.38
        mock_settings.semantic_intent_clarify_margin = 0.03

        det._vectors = vectors

        detected = []
        for message in group["messages"]:
            result = await det.detect(message, None)
            detected.append(result.intent_id)

        assert len(set(detected)) == 1
        assert detected[0] == expected_intent


def test_vector_db_shortlist_snapshot_stable_order():
    """Hard-filter + rank produces stable slug ordering for fixed constraints."""
    snapshot = load_vector_db_shortlist_snapshot()
    constraints = snapshot["constraints"]
    expected = snapshot["expected_slugs"]
    excluded = set(snapshot.get("excluded_slugs") or [])

    modules = [
        SimpleNamespace(slug="pinecone", name="Pinecone", tagline="", description="", pricing_model="paid", comparison_scores={"cost_efficiency": {"score": 5}}, technical_specs={}, supported_operations=[]),
        SimpleNamespace(slug="qdrant", name="Qdrant", tagline="", description="", pricing_model="open_source", comparison_scores={"cost_efficiency": {"score": 9}}, technical_specs={}, supported_operations=[]),
        SimpleNamespace(slug="weaviate", name="Weaviate", tagline="", description="", pricing_model="open_source", comparison_scores={"cost_efficiency": {"score": 8}}, technical_specs={}, supported_operations=[]),
        SimpleNamespace(slug="chromadb", name="ChromaDB", tagline="", description="", pricing_model="open_source", comparison_scores={"cost_efficiency": {"score": 7}}, technical_specs={}, supported_operations=[]),
        SimpleNamespace(slug="milvus", name="Milvus", tagline="", description="", pricing_model="open_source", comparison_scores={"cost_efficiency": {"score": 8}}, technical_specs={}, supported_operations=[]),
    ]

    from src.schemas.constraint_state import ConstraintSource, ConstraintState
    from src.services.pipelines.vector_db import VectorDbRecommendationPipeline

    state = ConstraintState()
    for key, value in constraints.items():
        state.set_slot(key, value, source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)

    pipeline = VectorDbRecommendationPipeline(db=None)  # type: ignore[arg-type]
    filtered, _removed = pipeline._filter(modules, state, None)  # type: ignore[arg-type]
    slugs_filtered = {m.slug for m in filtered}
    assert excluded.isdisjoint(slugs_filtered)

    top_slugs = pipeline.preview_shortlist(filtered, state, finalist_limit=len(expected))
    assert top_slugs == expected


@pytest.mark.asyncio
async def test_resolved_intent_skips_reclarification_for_short_followup():
    det = SemanticIntentDetector()
    result = await det.detect(
        "show integration code",
        {
            "active_task": "Help me build a RAG pipeline",
            "resolved_intent_id": "rag_pipeline",
            "active_playbook_id": "rag_pipeline_design",
        },
    )
    assert result.intent_id == "module_code"
    assert result.needs_clarification is False


def test_mock_router_assigns_one_vector_per_group():
    groups = load_paraphrase_groups()
    router = _mock_embedding_router()
    for group in groups:
        vecs = [router[m.strip().lower()] for m in group["messages"]]
        assert len({tuple(v) for v in vecs}) == 1
