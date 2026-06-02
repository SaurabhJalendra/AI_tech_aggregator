"""Streaming chaos scenarios (orchestration-level)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.schemas.intent import IntentResult
from src.services.chat_service import ChatService


@pytest.mark.asyncio
async def test_partial_sse_still_emits_done():
    service = ChatService(db=MagicMock())
    service.db.add = MagicMock()
    service.db.flush = AsyncMock()

    conversation = MagicMock()
    conversation.id = "00000000-0000-0000-0000-000000000001"
    conversation.message_count = 0
    user = MagicMock()
    user.id = "user-1"

    partial_events = [
        'data: {"type": "text", "content": "partial "}\n\n',
    ]

    with (
        patch("src.services.chat_service.settings") as mock_settings,
        patch(
            "src.services.recommendation_planner.RecommendationPlanner.plan",
            new_callable=AsyncMock,
            return_value=partial_events,
        ),
        patch("src.services.chat_service.get_semantic_intent_detector") as mock_det,
        patch("src.services.chat_service.load_user_profile", new_callable=AsyncMock, return_value={}),
        patch.object(service, "_persist_consulting_profile", new_callable=AsyncMock),
    ):
        mock_settings.planner_mode_normalized = "on"
        mock_settings.llm_fallback_enabled = False
        mock_det.return_value.detect = AsyncMock(
            return_value=IntentResult(
                intent_id="vector_db_comparison",
                confidence=0.9,
                margin=0.2,
                needs_clarification=False,
            )
        )

        chunks = []
        async for chunk in service.stream_response(
            user=user,
            session_id=None,
            message="compare vector databases",
            client_context={},
        ):
            chunks.append(chunk)

    types = []
    for c in chunks:
        if c.startswith("data: "):
            types.append(json.loads(c[6:].strip()).get("type"))
    assert "done" in types


@pytest.mark.asyncio
async def test_malformed_sse_line_skipped_without_crash():
    service = ChatService(db=MagicMock())
    events = service._sanitize_sse_event("data: not-json\n\n")
    assert events  # returns passthrough or empty, must not raise
