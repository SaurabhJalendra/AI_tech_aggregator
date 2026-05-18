"""Tests for deterministic chat constraint collection."""

import asyncio
import json
from types import SimpleNamespace

import pytest

from src.services.chat_service import ChatService
from src.services.recommendation_planner import RecommendationPlanner
from src.services.response_sanitizer import sanitize_advisor_text


def _decode_sse_events(events: list[str]) -> list[dict]:
    decoded = []
    for event in events:
        assert event.startswith("data: ")
        decoded.append(json.loads(event[6:].strip()))
    return decoded


def test_next_constraint_asks_for_implementation_preference_after_scale_and_budget():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]
    task = {
        "type": "rag_pipeline",
        "label": "RAG pipeline",
        "required_constraints": ["scale", "budget", "implementation_preference"],
    }

    question = planner.next_missing_question(task, {
        "scale": "growing_application",
        "budget": "low",
    })
    events = planner._option_card_events(task, question)

    assert events is not None
    decoded = _decode_sse_events(events)
    command = decoded[1]["command"]

    assert command["panel"] == "option_cards"
    assert command["data"]["question_id"] == "implementation_preference"
    assert command["data"]["options"][0]["metadata"] == {
        "implementation_preference": "python",
        "implementation_language": "python",
        "python_sdk": True,
    }


def test_extract_constraints_maps_python_to_implementation_preference():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]

    constraints = planner.extract_constraints(
        "I need Python SDK support",
        {
            "active_task": "Compare vector databases",
            "constraints": {
                "scale": "growing_application",
                "budget": "medium",
            },
        },
    )

    assert constraints["python_sdk"] is True
    assert constraints["implementation_preference"] == "python"
    assert constraints["implementation_language"] == "python"


def test_detects_rag_pipeline_and_requires_core_constraints():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]

    task = planner.detect_task(
        "Build me a RAG pipeline for ingestion, chunking, embeddings, storage, and retrieval.",
        None,
    )

    assert task is not None
    assert task["type"] == "rag_pipeline"
    assert task["required_constraints"] == [
        "scale",
        "budget",
        "implementation_preference",
    ]


def test_detects_llm_choice_with_quality_budget_and_sdk_constraints():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]

    task = planner.detect_task(
        "Help me choose an LLM with good reasoning and moderate cost.",
        None,
    )

    assert task is not None
    assert task["type"] == "category_comparison"
    assert task["category"] == "llm_layer"
    assert task["required_constraints"] == [
        "quality_priority",
        "budget",
        "implementation_preference",
    ]


def test_vector_database_constraints_do_not_ask_sdk_and_start_with_budget():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]

    task = planner.detect_task("Compare vector databases for my startup app", None)

    assert task is not None
    assert task["category"] == "vector_databases"
    assert task["required_constraints"] == [
        "budget",
        "scale",
        "deployment_preference",
    ]


def test_pick_vector_database_enters_planner_and_asks_budget_first():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]

    task = planner.detect_task("Help me pick a vector database.", None)
    question = planner.next_missing_question(task, {}) if task else None
    events = planner._option_card_events(task, question) if task and question else None

    assert task is not None
    assert task["type"] == "category_comparison"
    assert task["category"] == "vector_databases"
    assert question is not None
    assert question["id"] == "budget"

    decoded = _decode_sse_events(events)
    assert decoded[1]["command"]["panel"] == "option_cards"
    assert decoded[1]["command"]["data"]["question_id"] == "budget"
    assert "Traditional SQL" not in json.dumps(decoded[1])


def test_vector_database_low_budget_hard_filter_excludes_costly_candidates():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]
    modules = [
        SimpleNamespace(slug="qdrant"),
        SimpleNamespace(slug="weaviate"),
        SimpleNamespace(slug="chromadb"),
        SimpleNamespace(slug="milvus"),
        SimpleNamespace(slug="pinecone"),
    ]

    filtered = planner._apply_hard_filters(
        "vector_databases",
        modules,  # type: ignore[arg-type]
        {"budget": "low", "deployment_preference": "managed"},
    )

    assert [module.slug for module in filtered] == ["qdrant", "weaviate", "chromadb"]


def test_constraint_aware_recommendation_restates_startup_budget():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]

    recommendation = planner._constraint_aware_recommendation(
        {"label": "vector databases"},
        {"budget": "low", "scale": "growing_application", "deployment_preference": "managed"},
        ["qdrant", "weaviate"],
    )

    assert "startup budget" in recommendation
    assert "qdrant" in recommendation
    assert "Given your emphasis on scalability" not in recommendation


def test_detects_local_llm_agent_stack_and_asks_hardware_first():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]

    task = planner.detect_task(
        "I need an LLM with the absolute lowest cost and an agent framework that is self-hostable.",
        None,
    )
    question = planner.next_missing_question(task, {}) if task else None

    assert task is not None
    assert task["type"] == "local_ai_stack"
    assert question is not None
    assert question["id"] == "hardware"


def test_local_ai_stack_renders_architecture_before_code():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]

    events = planner._local_ai_stack_events({
        "hardware": "cpu_only",
        "agent_complexity": "single_agent",
    })

    decoded = _decode_sse_events(events)
    command = decoded[1]["command"]

    assert command["panel"] == "interactive_architecture"
    assert any(node["id"] == "ollama" for node in command["data"]["nodes"])
    assert all(command["panel"] != "code_project" for command in [command])


def test_option_card_text_is_contextual_not_repeated_canned_phrase():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]
    task = {"label": "vector databases"}

    budget_text = planner._constraint_question_text(task, "budget")
    scale_text = planner._constraint_question_text(task, "scale")

    assert budget_text != scale_text
    assert "Budget is the hard filter" in budget_text


@pytest.mark.asyncio
async def test_stream_with_keepalive_emits_event_during_idle_period():
    service = ChatService(db=None)  # type: ignore[arg-type]

    async def slow_stream():
        await asyncio.sleep(0.03)
        yield 'data: {"type": "done"}\n\n'

    events = []
    async for event in service._stream_with_keepalive(
        slow_stream(),
        interval_seconds=0.01,
    ):
        events.append(json.loads(event[6:].strip()))

    assert any(event["type"] == "keepalive" for event in events)
    assert events[-1]["type"] == "done"


def test_detects_architecture_review_before_rag_recommendation():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]

    task = planner.detect_task(
        "Check whether this RAG architecture is correct or not and what should be added.",
        {"current_panel": "interactive_architecture"},
    )

    assert task is not None
    assert task["type"] == "architecture_review"


def test_architecture_review_uses_interactive_panel_with_hover_compatible_nodes():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]

    events = planner._architecture_review_events({
        "current_panel_data": {
            "nodes": [
                {"id": "ingest", "label": "Unstructured OSS", "category": "data_ingestion"},
                {"id": "chunk", "label": "Semantic Chunking", "category": "chunking"},
                {"id": "store", "label": "Qdrant Cloud", "category": "vector_databases"},
            ]
        }
    })

    decoded = _decode_sse_events(events)
    command = decoded[1]["command"]
    node = command["data"]["nodes"][0]
    edge = command["data"]["edges"][0]

    assert command["panel"] == "interactive_architecture"
    assert {"id", "label", "category"}.issubset(node.keys())
    assert {"from", "to"}.issubset(edge.keys())
    assert any(n["id"] == "reranker" for n in command["data"]["nodes"])
    assert any(n["id"] == "observability" for n in command["data"]["nodes"])


def test_sanitizer_removes_ui_artifacts_and_uncited_metric_claims():
    text = """
    Good answer.
    ::view-transition-group(*) { animation-duration: 0.25s; }
    VvisualizeVvisualize show_widget
    This alone can improve answer quality by 20-30% in benchmarks.
    """

    cleaned = sanitize_advisor_text(text)

    assert "::view-transition" not in cleaned
    assert "show_widget" not in cleaned
    assert "Vvisualize" not in cleaned
    assert "20-30%" not in cleaned
    assert "Use benchmark data" in cleaned


def test_chat_service_sanitizes_text_sse_event():
    service = ChatService(db=None)  # type: ignore[arg-type]

    event = service._sanitize_sse_event(
        'data: {"type": "text", "content": "VvisualizeVvisualize show_widget"}\n\n'
    )

    decoded = json.loads(event[6:].strip())
    assert decoded["type"] == "text"
    assert decoded["content"].strip() == ""
