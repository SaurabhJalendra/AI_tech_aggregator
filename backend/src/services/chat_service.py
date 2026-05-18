"""Chat service — orchestrates the advisor agent and conversation management."""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.advisor import AdvisorAgent
from src.agent.prompts import build_catalog_section
from src.core.config import settings
from src.models.conversation import Conversation, Message
from src.models.module import Module, ModuleCategory
from src.models.user import User
from src.services.module_service import ModuleService
from src.services.recommendation_planner import RecommendationPlanner
from src.services.response_sanitizer import sanitize_advisor_text


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def stream_response(
        self,
        user: User,
        session_id: str | None,
        message: str,
        client_context: dict | None = None,
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

        # Emit session_id first
        yield f"data: {json.dumps({'type': 'meta', 'session_id': str(conversation.id)})}\n\n"

        collected_text = ""
        collected_panel_commands = []

        deterministic_events = await RecommendationPlanner(self.db).plan(
            message=message,
            client_context=client_context,
        )
        if deterministic_events:
            try:
                for sse_event in deterministic_events:
                    sse_event = self._sanitize_sse_event(sse_event)
                    yield sse_event
                    try:
                        if sse_event.startswith("data: "):
                            data = json.loads(sse_event[6:].strip())
                            if data.get("type") == "text":
                                collected_text += data.get("content", "")
                            elif data.get("type") == "panel_command":
                                collected_panel_commands.append(data.get("command"))
                    except (json.JSONDecodeError, KeyError):
                        pass
            finally:
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

                if conversation.message_count <= 2 and not conversation.title:
                    conversation.title = message[:100]

                await self.db.flush()
            return

        # Build messages for Claude only when deterministic planning cannot handle the turn.
        claude_messages = await self._build_claude_messages(conversation)
        if client_context:
            self._attach_client_context(claude_messages, client_context)

        # Get module/category counts and catalog for system prompt
        module_count = (
            await self.db.execute(select(func.count(Module.id)))
        ).scalar() or 0
        category_count = (
            await self.db.execute(select(func.count(ModuleCategory.id)))
        ).scalar() or 0

        # Build catalog section with all categories and module slugs
        module_svc = ModuleService(self.db)
        categories_with_slugs = await module_svc.list_categories_with_slugs()
        catalog_section = build_catalog_section(categories_with_slugs)

        # Run the advisor agent
        agent = AdvisorAgent(
            db=self.db,
            anthropic_api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            use_claude_code=settings.use_claude_code,
        )

        try:
            agent_stream = agent.stream_response(
                messages=claude_messages,
                module_count=module_count,
                category_count=category_count,
                catalog_section=catalog_section,
            )
            async for sse_event in self._stream_with_keepalive(agent_stream):
                sse_event = self._sanitize_sse_event(sse_event)
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

    async def _stream_with_keepalive(
        self,
        stream: AsyncGenerator[str, None],
        interval_seconds: float = 15,
    ) -> AsyncGenerator[str, None]:
        """Yield keepalive SSE events while a slow upstream stream is idle."""
        next_event = asyncio.create_task(anext(stream))
        try:
            while True:
                done, _ = await asyncio.wait({next_event}, timeout=interval_seconds)
                if not done:
                    yield self._sse_event("keepalive", {})
                    continue

                try:
                    event = next_event.result()
                except StopAsyncIteration:
                    break

                yield event
                next_event = asyncio.create_task(anext(stream))
        finally:
            if not next_event.done():
                next_event.cancel()
            aclose = getattr(stream, "aclose", None)
            if aclose:
                await aclose()

    def _sse_event(self, event_type: str, data: dict) -> str:
        payload = {"type": event_type, **data}
        return f"data: {json.dumps(payload)}\n\n"

    def _sanitize_sse_event(self, sse_event: str) -> str:
        if not sse_event.startswith("data: "):
            return sse_event

        try:
            data = json.loads(sse_event[6:].strip())
        except json.JSONDecodeError:
            return sse_event

        if data.get("type") == "text" and isinstance(data.get("content"), str):
            data["content"] = sanitize_advisor_text(data["content"])
            return f"data: {json.dumps(data)}\n\n"

        return sse_event

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

    def _attach_client_context(
        self,
        claude_messages: list[dict],
        client_context: dict,
    ) -> None:
        """Attach UI context to the latest user turn without changing stored chat text."""
        if not claude_messages:
            return

        latest = claude_messages[-1]
        if latest.get("role") != "user":
            return

        context_lines = self._format_client_context(client_context)
        if not context_lines:
            return

        latest["content"] = (
            f"{latest.get('content', '')}\n\n"
            "IMPORTANT UI CONTEXT: The text above may be a short option-card label. "
            "If an active task is present below, interpret this turn as a constraint "
            "answer for that task, not as a new standalone user request.\n"
            "<ui_context_for_reasoning_only>\n"
            f"{context_lines}\n"
            "</ui_context_for_reasoning_only>"
        )

    def _format_client_context(self, client_context: dict) -> str:
        """Make option-card context compact and hard for the model to ignore."""
        lines = []

        active_task = client_context.get("active_task")
        if active_task:
            lines.append(f"Active user task: {active_task}")

        option_answer = client_context.get("option_answer")
        if isinstance(option_answer, dict):
            question = option_answer.get("question")
            answer = option_answer.get("answer_label") or option_answer.get("answer_id")
            question_id = option_answer.get("question_id")
            if question or answer:
                lines.append(
                    "Latest option-card answer: "
                    f"question_id={question_id or 'unknown'}, "
                    f"question={question or 'unknown'}, "
                    f"answer={answer or 'unknown'}"
                )

            metadata = option_answer.get("metadata")
            if metadata:
                lines.append(f"Answer metadata: {json.dumps(metadata, sort_keys=True)}")

        constraints = client_context.get("constraints")
        if isinstance(constraints, dict) and constraints:
            lines.append(f"Accumulated constraints: {json.dumps(constraints, sort_keys=True)}")

        current_panel = client_context.get("current_panel")
        if current_panel:
            lines.append(f"Current right panel: {current_panel}")

        if lines:
            lines.append(
                "Instruction: the active task overrides the short option label. "
                "Continue toward the active task outcome. Do not branch into broad "
                "application discovery unless the active task explicitly asks for it."
            )

        return "\n".join(lines)

