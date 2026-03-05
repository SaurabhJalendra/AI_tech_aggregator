from fastapi import APIRouter, Depends, HTTPException
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
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Main chat endpoint. Streams SSE events with text + panel commands.
    """
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env",
        )

    chat_service = ChatService(db)

    return StreamingResponse(
        chat_service.stream_response(
            user=user,
            session_id=request.session_id,
            message=request.message,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
