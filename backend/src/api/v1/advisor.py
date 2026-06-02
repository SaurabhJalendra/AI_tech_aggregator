"""Advisor debug and Phase-2 trace utilities."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.advisor_playbooks.loader import list_playbooks
from src.core.security import get_current_user
from src.db.session import get_db
from src.models.conversation import Conversation, Message
from src.models.user import User
from src.schemas.advisor_trace import AdvisorTrace
from src.core.config import settings
from src.services.consulting_memory import list_evolution_history, load_user_profile
from src.core.security_context import abuse_snapshot
from src.services.planner_metrics import snapshot as planner_metrics_snapshot

router = APIRouter(prefix="/advisor", tags=["advisor"])


@router.get("/playbooks")
async def list_advisor_playbooks():
    """List declarative playbooks and phase2 migration flags."""
    playbooks = list_playbooks()
    return {
        "playbooks": [
            {
                "playbook_id": pid,
                "phase2_pipeline": bool(pb.get("phase2_pipeline")),
                "task_type": pb.get("task_type"),
            }
            for pid, pb in playbooks.items()
        ]
    }


@router.get("/trace/schema")
async def advisor_trace_schema():
    """JSON schema shape for AdvisorTrace payloads (debug clients)."""
    return AdvisorTrace.model_json_schema()


@router.get("/sessions/{session_id}/trace/latest")
async def latest_session_trace(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return the most recent persisted advisor trace for a conversation."""
    try:
        conv_id = uuid.UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid session_id") from exc

    conv = await db.get(Conversation, conv_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="session not found")

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_id, Message.role == "assistant")
        .order_by(Message.sequence_num.desc())
        .limit(20)
    )
    for msg in result.scalars():
        content = msg.content if isinstance(msg.content, dict) else {}
        trace = content.get("advisor_trace")
        if trace:
            return {
                "session_id": str(conv_id),
                "message_sequence": msg.sequence_num,
                "advisor_trace": trace,
                "recommendation_explain": content.get("recommendation_explain"),
                "constraint_state": content.get("constraint_state"),
            }
    return {"session_id": str(conv_id), "advisor_trace": None}


@router.get("/metrics/internal")
async def planner_health_metrics(
    user: User = Depends(get_current_user),
):
    """Internal-only planner health counters (not a user-facing dashboard)."""
    if settings.environment not in ("development", "staging"):
        raise HTTPException(status_code=403, detail="internal metrics disabled")
    return {
        "planner_health": planner_metrics_snapshot(),
        "security_context": abuse_snapshot(),
        "requested_by": user.email,
    }


@router.get("/consulting/profile")
async def get_consulting_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cross-session strategic consulting memory for the authenticated user."""
    profile = await load_user_profile(db, user)
    return {"consulting_profile": profile}


@router.get("/evolution/history")
async def get_evolution_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 15,
):
    """Architecture evolution timeline across sessions."""
    history = await list_evolution_history(db, user.id, limit=min(limit, 30))
    return {"evolution_history": history}
