"""Chat service — orchestrates the advisor agent and conversation management."""

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.advisor_playbooks.loader import resolve_playbook_id
from src.agent.advisor import AdvisorAgent
from src.agent.prompts import build_catalog_section
from src.core.config import settings
from src.models.conversation import Conversation, Message
from src.models.module import Module, ModuleCategory
from src.models.user import User
from src.services.module_service import ModuleService
from src.services.panel_validator import filter_llm_panel_command, validate_panel_command
from src.services.consulting_memory import (
    apply_profile_to_context,
    load_user_profile,
    merge_profile_from_state,
    persist_user_profile,
)
from src.services.recommendation_planner import RecommendationPlanner
from src.schemas.constraint_state import ConstraintState
from src.core.security_context import record_context_sanitization
from src.schemas.client_context import validate_client_context
from src.schemas.prompt_context import format_prompt_context
from src.services.planner_metrics import record_turn, snapshot as planner_metrics_snapshot
from src.services.planner_telemetry import (
    PlannerTurnTelemetry,
    compare_shadow_outcomes,
    log_planner_telemetry,
    summarize_planner_events,
)
from src.services.response_sanitizer import SanitizationReport, sanitize_advisor_text
from src.services.semantic_intent import (
    INTENT_LABELS,
    force_intent_result,
    get_semantic_intent_detector,
)

logger = logging.getLogger(__name__)


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
        stream_lifecycle: dict = {"started": True}

        merged_context, ctx_stats = validate_client_context(client_context)
        merged_context["session_id"] = str(conversation.id)
        security_flags = record_context_sanitization(
            ctx_stats,
            session_id=str(conversation.id),
        )
        planner_routing: dict = {
            "planner_mode": settings.planner_mode_normalized,
            "outcome": "pending",
        }
        telemetry = PlannerTurnTelemetry(
            planner_mode=settings.planner_mode_normalized,
            payload_stats={**ctx_stats.to_dict(), **security_flags},
            flat_constraints_rejected=bool(ctx_stats.flat_constraints_rejected),
            session_turn_index=conversation.message_count,
            stream_lifecycle=stream_lifecycle,
        )

        consulting_profile = await load_user_profile(self.db, user)
        apply_profile_to_context(consulting_profile, merged_context)

        clarification_choice = merged_context.get("intent_clarification_choice")
        if isinstance(clarification_choice, dict) and clarification_choice.get("intent_id"):
            forced_id = str(clarification_choice["intent_id"])
            intent_result = force_intent_result(forced_id)
            merged_context["resolved_intent_id"] = forced_id
            merged_context["awaiting_intent_clarification"] = False
            playbook_id = resolve_playbook_id(intent_id=forced_id)
            if playbook_id:
                merged_context["active_playbook_id"] = playbook_id
            logger.info("intent clarification choice intent_id=%s playbook=%s", forced_id, playbook_id)
        elif self._should_skip_semantic_intent(merged_context):
            forced_id = self._forced_intent_for_context(merged_context)
            intent_result = force_intent_result(forced_id)
            merged_context["resolved_intent_id"] = forced_id
            merged_context["awaiting_intent_clarification"] = False
            logger.info("skipped semantic intent for explicit planner action intent_id=%s", forced_id)
        else:
            intent_result = await get_semantic_intent_detector().detect(message, merged_context)

        self._apply_intent_to_context(merged_context, intent_result)
        telemetry.intent_id = intent_result.intent_id
        telemetry.routing_confidence = intent_result.confidence
        telemetry.playbook_id = merged_context.get("active_playbook_id")
        telemetry.constraint_snapshot = (
            merged_context.get("constraint_state", {}).get("slots", {})
            if isinstance(merged_context.get("constraint_state"), dict)
            else {}
        )

        if intent_result.needs_clarification and intent_result.clarification_prompt:
            telemetry.clarification_triggered = True
            clarification = intent_result.clarification_prompt
            alt_ids = [a.intent_id for a in intent_result.alternatives[:2]]
            if not alt_ids and intent_result.matched_evidence:
                alt_ids = list(
                    dict.fromkeys(e.intent_id for e in intent_result.matched_evidence[:2])
                )
            alt_playbooks = [
                resolve_playbook_id(intent_id=aid) for aid in alt_ids if aid
            ]
            for sse_event in (
                self._sse_event(
                    "meta",
                    {
                        "session_id": str(conversation.id),
                        "awaiting_intent_clarification": True,
                        "intent_alternatives": alt_ids,
                        "intent_alternative_labels": [
                            INTENT_LABELS.get(aid, aid) for aid in alt_ids
                        ],
                        "intent_alternative_playbooks": alt_playbooks,
                    },
                ),
                self._sse_event("text", {"content": clarification}),
                self._sse_event("done", {}),
            ):
                yield self._sanitize_sse_event(sse_event)
            assistant_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content={"text": clarification},
                panel_commands=None,
                sequence_num=conversation.message_count + 1,
            )
            self.db.add(assistant_msg)
            conversation.message_count += 1
            if conversation.message_count <= 2 and not conversation.title:
                conversation.title = message[:100]
            await self.db.flush()
            return

        merged_context["intent_result"] = intent_result.model_dump(mode="json")

        progress = self._planner_progress_message(merged_context, message)
        if progress:
            yield self._sse_event("text", {"content": progress})
            collected_text += progress

        planner_mode = settings.planner_mode_normalized
        deterministic_events = None
        shadow_planner_summary: dict | None = None
        if planner_mode != "off":
            deterministic_events = await RecommendationPlanner(self.db).plan(
                message=message,
                client_context=merged_context,
                intent_result=intent_result,
                user_id=user.id,
            )
            planner_routing["planner_ran"] = True
            planner_routing["planner_event_count"] = len(deterministic_events or [])
            shadow_planner_summary = summarize_planner_events(deterministic_events)
            trace = merged_context.get("advisor_trace")
            if isinstance(trace, dict):
                telemetry.pipeline_used = trace.get("playbook_id")
                shadow_planner_summary["shortlist"] = trace.get("shortlist")
            telemetry.deterministic_path = bool(deterministic_events)

        intercept = bool(deterministic_events) and planner_mode == "on"
        if intercept:
            planner_routing["outcome"] = "planner_intercepted"
            telemetry.intercepted = True
        elif deterministic_events and planner_mode == "shadow":
            planner_routing["outcome"] = "planner_shadow"
            yield self._sse_event(
                "meta",
                {
                    "planner_routing": planner_routing,
                    "planner_telemetry": telemetry.to_dict(),
                    "advisor_trace": merged_context.get("advisor_trace"),
                    "constraint_state": merged_context.get("constraint_state"),
                },
            )
        elif planner_mode == "off":
            planner_routing["outcome"] = "planner_off"
        else:
            planner_routing["outcome"] = "planner_skipped"

        logger.info(
            "planner_routing mode=%s outcome=%s events=%s",
            planner_routing.get("planner_mode"),
            planner_routing.get("outcome"),
            planner_routing.get("planner_event_count"),
        )

        router = "planner" if intercept else "agent"
        yield self._router_trace_event(
            router=router,
            planner_routing=planner_routing,
            intent_id=intent_result.intent_id,
            merged_context=merged_context,
        )

        if intercept:
            try:
                if (
                    merged_context.get("advisor_trace")
                    or merged_context.get("consulting_continuity")
                    or planner_routing
                ):
                    telemetry.intercepted = True
                    yield self._sse_event(
                        "meta",
                        {
                            "planner_routing": planner_routing,
                            "planner_telemetry": telemetry.to_dict(),
                            "advisor_trace": merged_context.get("advisor_trace"),
                            "recommendation_explain": merged_context.get("recommendation_explain"),
                            "constraint_state": merged_context.get("constraint_state"),
                            "consulting_continuity": merged_context.get("consulting_continuity"),
                            "consulting_profile": merged_context.get("consulting_profile"),
                        },
                    )
                for sse_event in deterministic_events:
                    sse_event = self._gate_planner_sse_event(sse_event)
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
                await self._persist_consulting_profile(user, consulting_profile, merged_context)
                if collected_text or collected_panel_commands:
                    content: dict = {"text": collected_text}
                    content["planner_telemetry"] = telemetry.to_dict()
                    if merged_context.get("advisor_trace"):
                        content["advisor_trace"] = merged_context["advisor_trace"]
                    if merged_context.get("recommendation_explain"):
                        content["recommendation_explain"] = merged_context["recommendation_explain"]
                    if merged_context.get("constraint_state"):
                        content["constraint_state"] = merged_context["constraint_state"]
                    record_turn(telemetry.to_dict())
                    log_planner_telemetry(telemetry, session_id=str(conversation.id))
                    assistant_msg = Message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=content,
                        panel_commands=collected_panel_commands if collected_panel_commands else None,
                        sequence_num=conversation.message_count + 1,
                    )
                    self.db.add(assistant_msg)
                    conversation.message_count += 1

                if conversation.message_count <= 2 and not conversation.title:
                    conversation.title = message[:100]

                await self.db.flush()
            yield self._sse_event("done", {})
            return

        telemetry.llm_used = True
        telemetry.fallback_reason = planner_routing.get("outcome")
        yield self._sse_event(
            "meta",
            {
                "planner_routing": {**planner_routing, "outcome": "llm_fallback"},
                "planner_telemetry": telemetry.to_dict(),
            },
        )

        planner = RecommendationPlanner(self.db)
        if not settings.llm_fallback_enabled:
            for sse_event in planner.playbook_guidance_fallback(message, merged_context) or self._text_only_fallback_events(
                "I need a bit more context to continue this advisor workflow."
            ):
                yield self._sanitize_sse_event(sse_event)
            return

        if settings.planner_authority_strict and merged_context.get("active_playbook_id"):
            fallback = planner.playbook_guidance_fallback(message, merged_context)
            if fallback:
                for sse_event in fallback:
                    yield self._sanitize_sse_event(sse_event)
                return

        # Build messages for Claude only when deterministic planning cannot handle the turn.
        claude_messages = await self._build_claude_messages(conversation)
        if merged_context:
            self._attach_client_context(
                claude_messages,
                merged_context,
                server_explain=merged_context.get("recommendation_explain"),
                server_trace=merged_context.get("advisor_trace"),
            )

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
            active_playbook = merged_context.get("active_playbook_id")
            has_evidence = bool(merged_context.get("recommendation_explain"))
            async for sse_event in self._stream_with_keepalive(agent_stream):
                sse_event = self._gate_llm_sse_event(
                    sse_event,
                    active_playbook_id=str(active_playbook) if active_playbook else None,
                    has_deterministic_evidence=has_evidence,
                )
                sse_event = self._sanitize_sse_event(sse_event)
                if not sse_event:
                    continue
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
            logger.exception("advisor_agent_stream_failed")
            stream_lifecycle["error"] = str(e)[:200]
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        finally:
            if planner_mode == "shadow" and shadow_planner_summary is not None:
                llm_summary = {
                    "panels": [
                        str(c.get("panel"))
                        for c in collected_panel_commands
                        if isinstance(c, dict)
                    ],
                    "text_length": len(collected_text),
                    "shortlist": merged_context.get("advisor_trace", {}).get("shortlist")
                    if isinstance(merged_context.get("advisor_trace"), dict)
                    else None,
                }
                shadow = compare_shadow_outcomes(shadow_planner_summary, llm_summary)
                telemetry.shadow_result = shadow
                telemetry.divergence_reason = shadow.get("divergence_reason")
                logger.info("planner_shadow_comparison %s", json.dumps(shadow, sort_keys=True))

            telemetry.stream_lifecycle = stream_lifecycle
            record_turn(telemetry.to_dict())
            log_planner_telemetry(telemetry, session_id=str(conversation.id))

            yield self._sse_event(
                "meta",
                {
                    "planner_telemetry": telemetry.to_dict(),
                    "planner_health": planner_metrics_snapshot(),
                },
            )
            yield self._sse_event("done", {})
            # Save assistant message (even if partial)
            if collected_text or collected_panel_commands:
                assistant_msg = Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content={
                        "text": collected_text,
                        "planner_telemetry": telemetry.to_dict(),
                    },
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

    def _apply_intent_to_context(self, merged_context: dict, intent_result) -> None:
        """Persist resolved intent + playbook on the turn context."""
        inferred = intent_result.inferred_parameters or {}
        if inferred.get("playbook_id"):
            merged_context["active_playbook_id"] = inferred["playbook_id"]
        elif intent_result.intent_id not in ("unknown", "ambiguous"):
            playbook_id = resolve_playbook_id(intent_id=intent_result.intent_id)
            if playbook_id:
                merged_context["active_playbook_id"] = playbook_id

        if intent_result.intent_id not in ("unknown", "ambiguous"):
            merged_context["resolved_intent_id"] = intent_result.intent_id

    def _gate_planner_sse_event(self, sse_event: str) -> str:
        if not sse_event.startswith("data: "):
            return sse_event
        try:
            data = json.loads(sse_event[6:].strip())
        except json.JSONDecodeError:
            return sse_event
        if data.get("type") != "panel_command":
            return sse_event
        command = data.get("command")
        ok, err = validate_panel_command(command)
        if not ok:
            logger.warning("planner panel command rejected: %s", err)
            return self._sse_event("text", {"content": "I could not render the next panel safely."})
        return sse_event

    def _gate_llm_sse_event(
        self,
        sse_event: str,
        *,
        active_playbook_id: str | None,
        has_deterministic_evidence: bool = False,
    ) -> str | None:
        if not sse_event.startswith("data: "):
            return sse_event
        try:
            data = json.loads(sse_event[6:].strip())
        except json.JSONDecodeError:
            return sse_event
        if data.get("type") != "panel_command":
            return sse_event
        command = data.get("command")
        filtered, reason = filter_llm_panel_command(
            command,
            active_playbook_id=active_playbook_id,
            planner_authority_strict=settings.planner_authority_strict,
            has_deterministic_evidence=has_deterministic_evidence,
        )
        if filtered is None:
            logger.info("LLM panel command dropped: %s", reason)
            return None
        data["command"] = {**filtered, "source": "llm"}
        return f"data: {json.dumps(data)}\n\n"

    def _text_only_fallback_events(self, text: str) -> list[str]:
        return [
            self._sse_event("text", {"content": text}),
            self._sse_event("done", {}),
        ]

    def _router_trace_event(
        self,
        *,
        router: str,
        planner_routing: dict,
        intent_id: str | None,
        merged_context: dict,
    ) -> str:
        """Explicit router observability for planner vs agent path (SSE consumers / tests)."""
        task = merged_context.get("active_task")
        if not isinstance(task, str):
            task = None
        return self._sse_event(
            "router_trace",
            {
                "router": router,
                "intent_id": intent_id,
                "playbook_id": merged_context.get("active_playbook_id"),
                "task": task,
                "outcome": planner_routing.get("outcome"),
                "planner_mode": planner_routing.get("planner_mode"),
            },
        )

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
            report = SanitizationReport()
            data["content"] = sanitize_advisor_text(data["content"], report=report)
            if report.actions:
                data["sanitization_trace"] = report.to_trace_events()
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
        *,
        server_explain: dict | None = None,
        server_trace: dict | None = None,
    ) -> None:
        """Attach UI context to the latest user turn without changing stored chat text."""
        if not claude_messages:
            return

        latest = claude_messages[-1]
        if latest.get("role") != "user":
            return

        safe_context, _ = validate_client_context(client_context)
        context_lines = format_prompt_context(
            safe_context,
            server_explain=server_explain if isinstance(server_explain, dict) else None,
            server_trace=server_trace if isinstance(server_trace, dict) else None,
        )
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

    @staticmethod
    def _should_skip_semantic_intent(client_context: dict) -> bool:
        """UI-driven planner actions should not block on embedding model load."""
        return bool(
            client_context.get("strategy_branch_id")
            or client_context.get("option_answer")
            or client_context.get("pin_current_strategy")
            or client_context.get("tradeoff_lever")
            or client_context.get("sandbox_posture")
            or client_context.get("compare_pin_ids")
            or client_context.get("intent_clarification_choice")
        )

    @staticmethod
    def _forced_intent_for_context(client_context: dict) -> str:
        resolved = client_context.get("resolved_intent_id")
        if resolved and resolved not in ("unknown", "ambiguous"):
            return str(resolved)
        playbook_id = client_context.get("active_playbook_id")
        if playbook_id == "rag_pipeline_design":
            return "rag_pipeline"
        if playbook_id == "local_ai_stack":
            return "local_ai_stack"
        if playbook_id and str(playbook_id).startswith("category_"):
            return str(playbook_id)
        return "rag_pipeline"

    @staticmethod
    def _planner_progress_message(client_context: dict, message: str) -> str | None:
        from src.services.strategic_consulting import (
            STRATEGY_BRANCHES,
            detect_strategy_branch_from_message,
        )

        branch_id = client_context.get("strategy_branch_id") or detect_strategy_branch_from_message(
            message
        )
        if branch_id:
            label = STRATEGY_BRANCHES.get(str(branch_id), {}).get("label", "strategy branch")
            return (
                f"Exploring **{label}** — re-scoring each pipeline stage for operational "
                f"consequences and tradeoffs…\n\n"
            )
        if client_context.get("pin_current_strategy"):
            return "Pinning this architecture to your strategy workspace…\n\n"
        if client_context.get("tradeoff_lever"):
            return "Applying that tradeoff lever to your blueprint…\n\n"
        if client_context.get("sandbox_posture"):
            return "Exploring that sandbox posture on your architecture…\n\n"
        return None

    async def _persist_consulting_profile(
        self,
        user: User,
        profile: dict,
        merged_context: dict,
    ) -> None:
        updated = dict(profile or {})
        raw = merged_context.get("constraint_state")
        if isinstance(raw, dict):
            try:
                state = ConstraintState.model_validate(raw)
                updated = merge_profile_from_state(updated, state)
            except Exception:
                pass
        ctx_profile = merged_context.get("consulting_profile")
        if isinstance(ctx_profile, dict):
            if ctx_profile.get("strategy_workspace"):
                updated["strategy_workspace"] = ctx_profile["strategy_workspace"]
            if ctx_profile.get("infrastructure_direction"):
                updated["infrastructure_direction"] = ctx_profile["infrastructure_direction"]
            if ctx_profile.get("slots"):
                updated["slots"] = {**updated.get("slots", {}), **ctx_profile.get("slots", {})}
        await persist_user_profile(self.db, user, updated)

