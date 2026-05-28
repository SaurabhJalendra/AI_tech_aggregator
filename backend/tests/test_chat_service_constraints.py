"""Tests for deterministic chat constraint collection."""

import asyncio
import json
from types import SimpleNamespace

from unittest.mock import patch

import pytest

from src.schemas.constraint_state import ConstraintSource, ConstraintState
from src.schemas.intent import IntentResult
from src.services.chat_service import ChatService
from src.services.constraint_state_service import ConstraintStateService
from src.services.recommendation_planner import RecommendationPlanner
from src.services.response_sanitizer import SanitizationReport, sanitize_advisor_text


def _state(flat: dict) -> ConstraintState:
    s = ConstraintState()
    for key, value in flat.items():
        if value is None:
            continue
        s.set_slot(key, value, source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    return s


def _decode_sse_events(events: list[str]) -> list[dict]:
    decoded = []
    for event in events:
        assert event.startswith("data: ")
        decoded.append(json.loads(event[6:].strip()))
    return decoded


def test_falsy_constraint_values_count_as_answered():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]
    task = {
        "type": "rag_pipeline",
        "label": "RAG pipeline",
        "required_constraints": ["scale", "budget", "implementation_preference"],
    }

    assert (
        planner.next_missing_question(
            task,
            _state({
                "scale": "growing_application",
                "budget": False,
                "implementation_preference": "python",
            }),
        )
        is None
    )

    missing = planner.next_missing_question(
        task,
        _state({"scale": "growing_application", "budget": 0}),
    )
    assert missing is not None
    assert missing["id"] == "implementation_preference"

    assert (
        planner.next_missing_question(
            task,
            _state({
                "scale": "growing_application",
                "budget": "",
                "implementation_preference": "",
            }),
        )
        is None
    )


def test_next_constraint_asks_for_implementation_preference_after_scale_and_budget():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]
    task = {
        "type": "rag_pipeline",
        "label": "RAG pipeline",
        "required_constraints": ["scale", "budget", "implementation_preference"],
    }

    question = planner.next_missing_question(
        task,
        _state({"scale": "growing_application", "budget": "low"}),
    )
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


def test_constraint_state_service_maps_python_from_message():
    state = ConstraintStateService.build(
        "I need Python SDK support",
        {
            "active_task": "Compare vector databases",
            "constraint_state": {
                "slots": {
                    "scale": {"value": "growing_application", "source": "explicit", "confidence": 1},
                    "budget": {"value": "medium", "source": "explicit", "confidence": 1},
                },
                "version": "1",
            },
        },
    )
    assert state.get("python_sdk") is True
    assert state.get("implementation_preference") == "python"
    assert state.get("implementation_language") == "python"


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
    question = planner.next_missing_question(task, ConstraintState()) if task else None
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


def test_pipeline_recommendation_restates_constraints():
    from types import SimpleNamespace

    from src.schemas.constraint_state import ConstraintSource, ConstraintState

    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]
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
    trace = SimpleNamespace(
        filtered_out=[SimpleNamespace(slug="pinecone")],
        scores=[SimpleNamespace(slug="qdrant", score=0.9)],
    )
    recommendation = planner._pipeline_recommendation(state, ["qdrant", "weaviate"], trace)

    assert "low" in recommendation.lower() or "budget" in recommendation.lower()
    assert "qdrant" in recommendation


def test_detects_local_llm_agent_stack_and_asks_hardware_first():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]

    task = planner.detect_task(
        "I need an LLM with the absolute lowest cost and an agent framework that is self-hostable.",
        None,
    )
    question = planner.next_missing_question(task, ConstraintState()) if task else None

    assert task is not None
    assert task["type"] == "local_ai_stack"
    assert question is not None
    assert question["id"] == "hardware"


@pytest.mark.asyncio
async def test_local_ai_stack_renders_architecture_before_code():
    from unittest.mock import AsyncMock, MagicMock

    from src.schemas.constraint_state import ConstraintSource, ConstraintState
    from src.services.pipelines.base import PipelineResult
    from src.schemas.advisor_trace import AdvisorTrace

    planner = RecommendationPlanner(db=MagicMock())
    state = ConstraintState()
    state.set_slot("hardware", "cpu_only", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    state.set_slot(
        "agent_complexity",
        "single_agent",
        source=ConstraintSource.EXPLICIT,
        confidence=1.0,
        force=True,
    )
    mock_pipeline = MagicMock()
    mock_pipeline.run = AsyncMock(
        return_value=PipelineResult(
            shortlist=["ollama"],
            weights={},
            trace=AdvisorTrace(playbook_id="local_ai_stack"),
            extra={
                "nodes": [{"id": "ollama", "label": "Ollama", "slug": "ollama"}],
                "edges": [],
            },
        )
    )
    with patch("src.services.recommendation_planner.get_pipeline", return_value=mock_pipeline):
        events = await planner._local_ai_stack_events_v2(state, {})

    decoded = _decode_sse_events(events)
    command = decoded[1]["command"]
    assert command["panel"] == "interactive_architecture"
    assert any(node["id"] == "ollama" for node in command["data"]["nodes"])


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


@pytest.mark.asyncio
async def test_module_code_request_renders_code_preview_not_scale_question():
    from unittest.mock import AsyncMock, MagicMock

    mock_module = MagicMock()
    mock_module.name = "Apache Tika"
    mock_module.slug = "apache_tika"
    mock_module.code_examples = [
        {
            "title": "Python Client with Tika Server",
            "language": "python",
            "code": "import requests\n",
        }
    ]

    planner = RecommendationPlanner(db=MagicMock())  # type: ignore[arg-type]
    planner.module_service = MagicMock()
    planner.module_service.get_by_slug = AsyncMock(return_value=mock_module)
    planner.module_service.list_modules = AsyncMock(return_value=([mock_module], 1))

    client_context = {
        "active_task": "Help me build a RAG pipeline with solid architecture",
        "current_panel": "interactive_architecture",
        "constraints": {
            "scale": "enterprise",
            "budget": "high",
            "implementation_preference": "python",
        },
        "focus_module_slug": "apache_tika",
    }

    task = planner.detect_task(
        "Show me integration code for Apache Tika",
        client_context,
    )
    assert task is not None
    assert task["type"] == "module_code"

    from unittest.mock import patch

    from src.services.pipelines.base import PipelineResult
    from src.schemas.advisor_trace import AdvisorTrace

    mock_result = PipelineResult(
        shortlist=["apache_tika"],
        weights={},
        trace=AdvisorTrace(playbook_id="module_code"),
        extra={"module": mock_module},
    )

    with patch(
        "src.services.pipelines.module_code.ModuleCodePipeline.run",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        events = await planner.plan(
            "Show me integration code for Apache Tika",
            client_context,
            IntentResult(
                intent_id="module_code",
                confidence=0.95,
                margin=1.0,
                matched_evidence=[],
                inferred_parameters={},
            ),
        )

    assert events is not None
    decoded = _decode_sse_events(events)
    cmd = decoded[1]["command"]
    assert cmd["panel"] == "interactive_architecture"
    assert cmd["action"] == "update"
    assert "import requests" in cmd["data"]["codeDrawer"]["code"]
    assert cmd["data"]["codeDrawer"]["language"] == "python"


def test_detects_architecture_review_before_rag_recommendation():
    planner = RecommendationPlanner(db=None)  # type: ignore[arg-type]

    task = planner.detect_task(
        "Check whether this RAG architecture is correct or not and what should be added.",
        {"current_panel": "interactive_architecture"},
    )

    assert task is not None
    assert task["type"] == "architecture_review"


@pytest.mark.asyncio
async def test_architecture_review_uses_interactive_panel_with_hover_compatible_nodes():
    from unittest.mock import AsyncMock, MagicMock

    from src.schemas.constraint_state import ConstraintState
    from src.services.pipelines.architecture_review import ArchitectureReviewPipeline
    from src.services.pipelines.base import PipelineResult
    from src.schemas.advisor_trace import AdvisorTrace

    planner = RecommendationPlanner(db=MagicMock())
    state = ConstraintState()
    client_context = {
        "current_panel_data": {
            "nodes": [
                {"id": "ingest", "label": "Unstructured OSS", "category": "data_ingestion"},
                {"id": "chunk", "label": "Semantic Chunking", "category": "chunking"},
                {"id": "store", "label": "Qdrant Cloud", "category": "vector_databases"},
            ]
        }
    }
    mock_pipeline = MagicMock(spec=ArchitectureReviewPipeline)
    mock_pipeline.run = AsyncMock(
        return_value=PipelineResult(
            shortlist=[],
            weights={},
            trace=AdvisorTrace(playbook_id="architecture_review"),
            extra={"findings": [{"severity": "critical", "message": "Missing reranker"}]},
        )
    )
    with patch(
        "src.services.pipelines.architecture_review.ArchitectureReviewPipeline",
        return_value=mock_pipeline,
    ):
        events = await planner._architecture_review_events_v2(client_context, state)

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

    report = SanitizationReport()
    cleaned = sanitize_advisor_text(text, report=report)

    assert "::view-transition" not in cleaned
    assert "show_widget" not in cleaned
    assert "Vvisualize" not in cleaned
    assert "20-30%" in cleaned
    assert any(a.rule == "uncited_metric_claim_flagged" for a in report.actions)


def test_chat_service_sanitizes_text_sse_event():
    service = ChatService(db=None)  # type: ignore[arg-type]

    event = service._sanitize_sse_event(
        'data: {"type": "text", "content": "VvisualizeVvisualize show_widget"}\n\n'
    )

    decoded = json.loads(event[6:].strip())
    assert decoded["type"] == "text"
    assert decoded["content"].strip() == ""
