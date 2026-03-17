import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_current_user
from src.db.session import get_db
from src.models.conversation import Conversation, Message
from src.models.user import User

router = APIRouter(tags=["sessions"])


@router.get("/sessions")
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    limit: int | None = Query(None, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's conversation sessions."""
    effective_limit = limit if limit is not None else page_size

    base_query = select(Conversation).where(
        Conversation.user_id == user.id
    ).order_by(Conversation.updated_at.desc())

    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    if limit is not None:
        query = base_query.limit(limit)
    else:
        query = base_query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    conversations = result.scalars().all()

    return {
        "sessions": [
            {
                "id": str(c.id),
                "title": c.title or "Untitled Conversation",
                "summary": c.summary,
                "message_count": c.message_count,
                "total_tokens": c.total_tokens,
                "total_cost_usd": float(c.total_cost_usd),
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in conversations
        ],
        "total": total,
        "page": page,
        "page_size": effective_limit,
    }


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages for a conversation session."""
    try:
        conv_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    conversation = (await db.execute(
        select(Conversation).where(
            Conversation.id == conv_uuid,
            Conversation.user_id == user.id,
        )
    )).scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (await db.execute(
        select(Message)
        .where(Message.conversation_id == conv_uuid)
        .order_by(Message.sequence_num)
    )).scalars().all()

    return [
        {
            "role": msg.role,
            "content": msg.content.get("text", "") if msg.content else "",
            "panel_commands": msg.panel_commands or [],
            "created_at": str(msg.created_at) if msg.created_at else None,
        }
        for msg in messages
    ]


@router.get("/users/me")
async def get_user_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user profile with usage stats."""
    from datetime import date, datetime, timezone

    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)

    total_conversations = (await db.execute(
        select(func.count()).select_from(
            select(Conversation.id).where(Conversation.user_id == user.id).subquery()
        )
    )).scalar() or 0

    today_conversations = (await db.execute(
        select(func.count()).select_from(
            select(Conversation.id).where(
                Conversation.user_id == user.id,
                Conversation.created_at >= today_start,
            ).subquery()
        )
    )).scalar() or 0

    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "tier": user.tier,
        "conversations_today": today_conversations,
        "conversations_total": total_conversations,
        "comparisons_total": 0,
        "tokens_used_today": 0,
        "cost_today_usd": 0.0,
    }
