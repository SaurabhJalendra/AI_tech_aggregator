"""Chat service — orchestrates the advisor agent and conversation management."""

import json
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.advisor import AdvisorAgent
from src.core.config import settings
from src.models.conversation import Conversation, Message
from src.models.module import Module, ModuleCategory
from src.models.user import User


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def stream_response(
        self,
        user: User,
        session_id: str | None,
        message: str,
    ) -> AsyncGenerator[str, None]:
        """
        Handle a chat message: manage conversation, run agent, stream response.
        """
        # Get or create conversation
        conversation = await self._get_or_create_conversation(user, session_id)

        # Get current message count for sequence numbering
        msg_count = conversation.message_count or 0

        # Save user message
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content={"text": message},
            sequence_num=msg_count + 1,
        )
        self.db.add(user_msg)
        conversation.message_count = msg_count + 1
        await self.db.flush()

        # Build messages for Claude from conversation history
        claude_messages = await self._build_claude_messages(conversation)

        # Get module/category counts for system prompt
        module_count = (
            await self.db.execute(select(func.count(Module.id)))
        ).scalar() or 0
        category_count = (
            await self.db.execute(select(func.count(ModuleCategory.id)))
        ).scalar() or 0

        # Emit session_id first
        yield f"data: {json.dumps({'type': 'meta', 'session_id': str(conversation.id)})}\n\n"

        # Run the advisor agent
        agent = AdvisorAgent(
            db=self.db,
            anthropic_api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            use_claude_code=settings.use_claude_code,
        )

        collected_text = ""
        collected_panel_commands = []

        try:
            async for sse_event in agent.stream_response(
                messages=claude_messages,
                module_count=module_count,
                category_count=category_count,
            ):
                yield sse_event

                # Parse the event to collect text/commands for saving
                try:
                    if sse_event.startswith("data: "):
                        data = json.loads(sse_event[6:].strip())
                        if data.get("type") == "text":
                            collected_text += data.get("content", "")
                        elif data.get("type") == "panel_command":
                            collected_panel_commands.append(data.get("command"))
                except (json.JSONDecodeError, KeyError):
                    pass
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        finally:
            # Save assistant message (even if partial)
            if collected_text or collected_panel_commands:
                assistant_msg = Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content={"text": collected_text},
                    panel_commands=collected_panel_commands if collected_panel_commands else None,
                    sequence_num=conversation.message_count + 1,
                )
                self.db.add(assistant_msg)
                conversation.message_count += 1

            # Update conversation title if it's the first exchange
            if conversation.message_count <= 2 and not conversation.title:
                conversation.title = message[:100]

            await self.db.flush()

    async def _get_or_create_conversation(
        self, user: User, session_id: str | None
    ) -> Conversation:
        """Get existing conversation or create new one."""
        if session_id:
            try:
                conv_uuid = uuid.UUID(session_id)
                result = await self.db.execute(
                    select(Conversation).where(
                        Conversation.id == conv_uuid,
                        Conversation.user_id == user.id,
                    )
                )
                conversation = result.scalar_one_or_none()
                if conversation:
                    return conversation
            except ValueError:
                pass

        # Create new conversation
        conversation = Conversation(
            user_id=user.id,
            status="active",
        )
        self.db.add(conversation)
        await self.db.flush()
        return conversation

    async def _build_claude_messages(self, conversation: Conversation) -> list[dict]:
        """Build Claude-compatible message history from conversation."""
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.sequence_num)
        )
        messages_db = result.scalars().all()

        claude_messages = []
        for msg in messages_db:
            if msg.role == "user":
                claude_messages.append({
                    "role": "user",
                    "content": msg.content.get("text", ""),
                })
            elif msg.role == "assistant":
                claude_messages.append({
                    "role": "assistant",
                    "content": msg.content.get("text", ""),
                })

        return claude_messages
