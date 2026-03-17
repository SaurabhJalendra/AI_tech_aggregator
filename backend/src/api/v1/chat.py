from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import get_current_user
from src.db.session import get_db
from src.models.user import User
from src.schemas.chat import ChatRequest

from src.services.chat_service import ChatService

router = APIRouter(tags=["chat"])


@router.post("/advisor/chat")
async def advisor_chat(
    request: Request,
    chat_request: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Main chat endpoint. Streams SSE events with text + panel commands.
    """
    if not settings.use_claude_code and not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env or enable USE_CLAUDE_CODE=true",
        )

    chat_service = ChatService(db)

    return StreamingResponse(
        chat_service.stream_response(
            user=user,
            session_id=chat_request.session_id,
            message=chat_request.message,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
