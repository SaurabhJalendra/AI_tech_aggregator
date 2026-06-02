"""System-level advisor hardening regression (mocked DB, real orchestration)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.schemas.constraint_state import ConstraintSource, ConstraintState
from src.schemas.intent import IntentResult
from src.services.chat_service import ChatService
from src.services.constraint_state_service import ConstraintStateService
from src.services.recommendation_planner import RecommendationPlanner


@pytest.mark.asyncio
async def test_constraint_state_persists_across_turns_via_service():
    prior = ConstraintState(playbook_id="vector_db_comparison")
    prior.set_slot("budget", "low", source=ConstraintSource.OPTION_CARD, confidence=1.0, force=True)

    state = ConstraintStateService.build(
        "managed deployment please",
        {
            "constraint_state": prior.model_dump(mode="json"),
            "active_playbook_id": "vector_db_comparison",
        },
        playbook_id="vector_db_comparison",
    )
    assert state.get("budget") == "low"
    assert state.has("deployment_preference") or "managed" in "managed deployment please"


@pytest.mark.asyncio
async def test_planner_negotiation_on_filter_exhausted():
    planner = RecommendationPlanner(db=MagicMock())
    state = ConstraintState()
    state.set_slot("budget", "low", source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    state.set_slot(
        "deployment_preference",
        "self_hosted",
        source=ConstraintSource.EXPLICIT,
        confidence=1.0,
        force=True,
    )

    pipeline = MagicMock()
    pipeline.run = AsyncMock(
        return_value=MagicMock(
            shortlist=[],
            weights={},
            trace=MagicMock(
                model_dump=lambda mode="json": {"playbook_id": "vector_db_comparison", "filtered_out": []},
                to_explain_payload=lambda: {},
                steps=[],
            ),
            extra={"filter_exhausted": True, "message": "no match"},
        )
    )

    task = {"label": "Vector DB comparison", "type": "vector_db_comparison"}
    client_context: dict = {}

    with patch(
        "src.services.recommendation_planner.VectorDbRecommendationPipeline",
        return_value=pipeline,
    ):
        events = await planner._vector_db_comparison_events(task, state, client_context)

    assert events is not None
    decoded = [json.loads(e[6:].strip()) for e in events if e.startswith("data: ")]
    panel = next(d["command"] for d in decoded if d.get("type") == "panel_command")
    assert panel["panel"] == "option_cards"
    assert panel["data"]["question_id"] == "constraint_negotiation"


@pytest.mark.asyncio
async def test_chat_stream_emits_planner_telemetry_on_intercept():
    service = ChatService(db=MagicMock())
    service.db.add = MagicMock()
    service.db.flush = AsyncMock()

    conversation = MagicMock()
    conversation.id = "00000000-0000-0000-0000-000000000001"
    conversation.message_count = 0
    user = MagicMock()
    user.id = "user-1"

    planner_events = [
        'data: {"type": "text", "content": "Deterministic result"}\n\n',
        'data: {"type": "done"}\n\n',
    ]

    with (
        patch("src.services.chat_service.settings") as mock_settings,
        patch(
            "src.services.recommendation_planner.RecommendationPlanner.plan",
            new_callable=AsyncMock,
            return_value=planner_events,
        ),
        patch("src.services.chat_service.get_semantic_intent_detector") as mock_det,
        patch("src.services.chat_service.load_user_profile", new_callable=AsyncMock, return_value={}),
        patch.object(service, "_persist_consulting_profile", new_callable=AsyncMock),
    ):
        mock_settings.planner_mode_normalized = "on"
        mock_settings.llm_fallback_enabled = True
        mock_det.return_value.detect = AsyncMock(
            return_value=IntentResult(
                intent_id="vector_db_comparison",
                confidence=0.9,
                margin=0.2,
                needs_clarification=False,
            )
        )

        metas = []
        async for chunk in service.stream_response(
            user=user,
            session_id=None,
            message="compare vector databases",
            client_context={"constraint_state": {"slots": {}, "version": "1"}},
        ):
            if chunk.startswith("data: "):
                data = json.loads(chunk[6:].strip())
                if data.get("type") == "meta" and data.get("planner_telemetry"):
                    metas.append(data["planner_telemetry"])

    assert metas
    assert metas[-1].get("intercepted") is True
