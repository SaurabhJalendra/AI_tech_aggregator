"""Deterministic planning layer for advisor recommendations."""

import json
import logging
import re
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.advisor_playbooks.loader import (
    get_playbook,
    playbook_required_slots,
    resolve_playbook_id,
)
from src.core.config import settings
from src.models.module import Module
from src.modules.comparison_engine import ComparisonEngine
from src.schemas.intent import IntentResult
from src.schemas.constraint_state import ConstraintState
from src.services.constraint_state_service import ConstraintStateService
from src.services.module_service import ModuleService
from src.services.pipeline_registry import get_pipeline
from src.services.architecture_consulting import build_architecture_consulting
from src.services.architecture_simulation import (
    apply_simulation_to_state,
    build_simulation_narrative,
    detect_architecture_simulation,
)
from src.services.consulting_memory import (
    get_pinned_strategies,
    list_evolution_history,
    pin_current_architecture,
    record_evolution_snapshot,
)
from src.services.phase6_intelligence import (
    SANDBOX_POSTURES,
    TRADEOFF_LEVERS,
    apply_tradeoff_lever,
)
from src.services.strategic_consulting import (
    apply_branch_slots,
    build_dual_strategy_comparison,
    detect_dual_strategy_request,
    enrich_architecture_consulting,
)
from src.services.pipelines.base import attach_pipeline_context
from src.services.pipelines.vector_db import VectorDbRecommendationPipeline
from src.services.comparison_universe import (
    apply_comparison_layer_to_state,
    get_layer_label,
    resolve_comparison_layer,
)
from src.services.slot_impact_policy import SlotImpactPolicy

logger = logging.getLogger(__name__)


CATEGORY_ALIASES = {
    "vector_databases": (
        "vector database",
        "vector db",
        "vector store",
        "pinecone",
        "qdrant",
        "weaviate",
        "milvus",
    ),
    "llm_layer": (
        "llm",
        "language model",
        "reasoning model",
        "model",
        "claude",
        "openai",
        "latency",
    ),
    "embeddings": ("embedding", "embeddings", "embed"),
    "chunking": ("chunk", "chunking", "splitter", "splitting"),
    "data_ingestion": ("ingestion", "parse", "parser", "pdf", "document loading"),
    "retrieval": ("retrieval", "rerank", "hybrid search", "search"),
    "evaluation": ("evaluation", "eval", "ragas", "benchmark"),
    "deployment": ("deploy", "deployment", "hosting", "production"),
    "agent_systems": ("agent framework", "agent frameworks", "agent", "crewai", "autogen", "langgraph"),
}

COMPARISON_DIMENSIONS = [
    "performance",
    "scalability",
    "ease_of_use",
    "cost_efficiency",
    "community",
    "maturity",
    "flexibility",
    "data_privacy",
]

RAG_PIPELINE = [
    "data_ingestion",
    "chunking",
    "embeddings",
    "vector_databases",
    "retrieval",
    "llm_layer",
    "evaluation",
    "deployment",
]


class RecommendationPlanner:
    """Owns deterministic advisor flow before the LLM fallback runs."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.module_service = ModuleService(db)
        self.comparison_engine = ComparisonEngine(db)

    async def plan(
        self,
        message: str,
        client_context: dict | None,
        intent_result: IntentResult | None = None,
        user_id: uuid.UUID | None = None,
    ) -> list[str] | None:
        task = self.detect_task(message, client_context, intent_result)
        if not task:
            return self.playbook_guidance_fallback(message, client_context)

        playbook_id = task.get("playbook_id")
        state = ConstraintStateService.build(
            message,
            client_context,
            playbook_id=str(playbook_id) if playbook_id else None,
        )
        if client_context is not None:
            client_context["constraint_state"] = state.model_dump(mode="json")

        pb_id = playbook_id or (
            "vector_db_comparison"
            if task.get("category") == "vector_databases"
            else f"category_{task.get('category', 'unknown')}"
        )
        missing_question = await SlotImpactPolicy(self.db).next_impactful_question(
            pb_id,
            state,
            task["required_constraints"],
            self.constraint_questions(),
            category=task.get("category"),
        )

        if missing_question:
            if client_context is not None:
                client_context["advisor_trace"] = {
                    "playbook_id": playbook_id,
                    "missing_slot_asked": missing_question["id"],
                    "constraint_snapshot": state.model_dump(mode="json"),
                    "steps": [f"slot_policy: ask {missing_question['id']}"],
                }
            return self._option_card_events(task, missing_question)

        workspace_events = await self._maybe_workspace_action_events(
            message, client_context, state, user_id=user_id
        )
        if workspace_events:
            return workspace_events

        branch_events = await self._maybe_strategy_branch_events(
            message, client_context, state, user_id=user_id
        )
        if branch_events:
            return branch_events

        dual_events = await self._maybe_dual_strategy_events(
            message, client_context, state, user_id=user_id
        )
        if dual_events:
            return dual_events

        sim_events = await self._maybe_architecture_simulation_events(
            message, client_context, state, intent_result=intent_result, user_id=user_id
        )
        if sim_events:
            return sim_events

        if task["type"] == "module_code":
            return await self._module_code_events_v2(message, client_context, state)

        if task["type"] == "architecture_review":
            return await self._architecture_review_events_v2(client_context, state)

        if task["type"] == "rag_pipeline" or playbook_id == "rag_pipeline_design":
            return await self._rag_pipeline_events_v2(
                task, state, client_context, user_id=user_id
            )

        if task["type"] == "category_comparison":
            return await self._category_comparison_events_v2(
                message, task, state, client_context
            )

        if task["type"] == "local_ai_stack" or playbook_id == "local_ai_stack":
            return await self._local_ai_stack_events_v2(state, client_context)

        return self.playbook_guidance_fallback(message, client_context)

    def playbook_guidance_fallback(
        self,
        message: str,
        client_context: dict | None,
    ) -> list[str] | None:
        """Text-only continuation when no deterministic branch matched but playbook is active."""
        if not client_context:
            return None
        playbook_id = client_context.get("active_playbook_id")
        if not playbook_id:
            return None
        playbook = get_playbook(str(playbook_id))
        if not playbook:
            return None
        label = str(playbook.get("task_type", playbook_id)).replace("_", " ")
        text = (
            f"I'm continuing the **{label}** workflow from your earlier choices. "
            "Use the panel, option cards, or name a specific module for a focused follow-up."
        )
        logger.info(
            "planner playbook fallback playbook_id=%s message_len=%d",
            playbook_id,
            len(message),
        )
        return self._text_only_events(text)

    def detect_task(
        self,
        message: str,
        client_context: dict | None,
        intent_result: IntentResult | None = None,
    ) -> dict | None:
        heuristic = self._detect_task_heuristic(message, client_context)
        if intent_result is None or intent_result.intent_id in ("unknown", "ambiguous"):
            return self._attach_playbook_metadata(heuristic) if heuristic else None

        semantic = self._task_from_intent_result(intent_result)
        merged = self._merge_heuristic_and_semantic(heuristic, semantic, intent_result)
        return self._attach_playbook_metadata(merged) if merged else None

    def _attach_playbook_metadata(self, task: dict | None) -> dict | None:
        if not task:
            return None
        playbook_id = resolve_playbook_id(
            task_type=task.get("type"),
            category=task.get("category"),
        )
        if playbook_id:
            task["playbook_id"] = playbook_id
            slots = playbook_required_slots(playbook_id)
            if slots:
                task["required_constraints"] = slots
        return task

    def _detect_task_heuristic(self, message: str, client_context: dict | None) -> dict | None:
        active_task = ""
        if client_context:
            active_task = str(client_context.get("active_task") or "")

        combined = f"{active_task} {message}".lower()
        has_option_answer = bool(
            client_context and isinstance(client_context.get("option_answer"), dict)
        )

        if self._is_module_code_request(combined, client_context):
            return {
                "type": "module_code",
                "label": "module integration code",
                "required_constraints": [],
            }

        if self._is_architecture_review_request(combined, client_context):
            return {
                "type": "architecture_review",
                "label": "architecture review",
                "required_constraints": [],
            }

        if self._is_local_llm_agent_stack_request(combined):
            return {
                "type": "local_ai_stack",
                "label": "local LLM + agent stack",
                "required_constraints": ["hardware", "agent_complexity"],
            }

        if "rag" in combined or "retrieval augmented" in combined:
            return {
                "type": "rag_pipeline",
                "label": "RAG pipeline",
                "required_constraints": [
                    "scale",
                    "budget",
                    "implementation_preference",
                ],
            }

        if any(
            term in combined
            for term in (
                "designing",
                "design a",
                "design an",
                "design the",
                "build a pipeline",
                "end to end",
                "end-to-end",
            )
        ) and any(term in combined for term in ("rag", "pipeline", "retrieval", "ingestion")):
            return {
                "type": "rag_pipeline",
                "label": "RAG pipeline",
                "required_constraints": [
                    "scale",
                    "budget",
                    "implementation_preference",
                ],
            }

        category = self._detect_category(combined)
        if not category:
            return None

        wants_recommendation = any(
            term in combined
            for term in (
                "compare",
                "comparison",
                "choose",
                "pick",
                "select",
                "recommend",
                "best",
                "show",
            )
        )
        if not wants_recommendation and not has_option_answer:
            return None

        return {
            "type": "category_comparison",
            "category": category,
            "label": category.replace("_", " "),
            "required_constraints": self._required_constraints_for_category(category),
        }

    def _task_from_intent_result(self, intent_result: IntentResult) -> dict | None:
        iid = intent_result.intent_id
        if iid == "module_code":
            return {
                "type": "module_code",
                "label": "module integration code",
                "required_constraints": [],
            }
        if iid == "architecture_review":
            return {
                "type": "architecture_review",
                "label": "architecture review",
                "required_constraints": [],
            }
        if iid == "local_ai_stack":
            return {
                "type": "local_ai_stack",
                "label": "local LLM + agent stack",
                "required_constraints": ["hardware", "agent_complexity"],
            }
        if iid == "rag_pipeline":
            return {
                "type": "rag_pipeline",
                "label": "RAG pipeline",
                "required_constraints": [
                    "scale",
                    "budget",
                    "implementation_preference",
                ],
            }
        if iid.startswith("category:"):
            cat = iid.split(":", 1)[1]
            return {
                "type": "category_comparison",
                "category": cat,
                "label": cat.replace("_", " "),
                "required_constraints": self._required_constraints_for_category(cat),
            }
        return None

    def _merge_heuristic_and_semantic(
        self,
        heuristic: dict | None,
        semantic: dict | None,
        intent_result: IntentResult,
    ) -> dict | None:
        if intent_result.intent_id in ("unknown", "ambiguous"):
            return heuristic
        if semantic is None:
            return heuristic
        if intent_result.confidence < settings.semantic_intent_min_confidence:
            return heuristic

        if heuristic and semantic:
            st = semantic["type"]
            if st in ("module_code", "architecture_review") and intent_result.intent_id == st:
                return semantic
        if heuristic:
            ht = heuristic["type"]
            if ht in ("module_code", "architecture_review", "local_ai_stack", "rag_pipeline"):
                return self._attach_playbook_metadata(heuristic)
            if ht == "category_comparison":
                if (
                    semantic["type"] == "category_comparison"
                    and intent_result.confidence >= settings.semantic_intent_override_confidence
                    and intent_result.margin is not None
                    and intent_result.margin >= settings.semantic_intent_override_margin
                    and semantic["category"] != heuristic["category"]
                ):
                    return semantic
                return heuristic

        return semantic

    def _is_local_llm_agent_stack_request(self, combined: str) -> bool:
        wants_llm = any(term in combined for term in ("llm", "language model", "model"))
        wants_agent = any(
            term in combined
            for term in ("agent", "agent framework", "crewai", "autogen", "langgraph")
        )
        wants_local_or_low_cost = any(
            term in combined
            for term in (
                "lowest cost",
                "absolute lowest",
                "zero cost",
                "free",
                "self-host",
                "self host",
                "privacy",
                "local",
            )
        )
        return wants_llm and wants_agent and wants_local_or_low_cost

    def next_missing_question(self, task: dict, state: ConstraintState) -> dict | None:
        questions = self.constraint_questions()
        for question_id in task["required_constraints"]:
            if state.has(question_id):
                continue
            question = questions[question_id]
            return {"id": question_id, **question}
        return None

    def _is_architecture_review_request(
        self,
        combined: str,
        client_context: dict | None,
    ) -> bool:
        is_review = any(
            term in combined
            for term in (
                "check",
                "review",
                "correct or not",
                "what should be added",
                "what is the issue",
                "issues with",
                "missing",
            )
        )
        mentions_architecture = "architecture" in combined or "diagram" in combined
        has_architecture_panel = bool(
            client_context
            and client_context.get("current_panel")
            in {"architecture_diagram", "interactive_architecture"}
        )
        return is_review and (mentions_architecture or has_architecture_panel)

    def constraint_questions(self) -> dict[str, dict]:
        return {
            "scale": {
                "question": "What scale should I optimize for?",
                "options": [
                    {
                        "id": "prototype",
                        "label": "Prototype / Demo",
                        "description": "Small dataset, low query volume, experimenting",
                        "icon": "beaker",
                        "metadata": {"scale": "prototype"},
                    },
                    {
                        "id": "growing_application",
                        "label": "Growing Application",
                        "description": "Production-ready with moderate traffic",
                        "icon": "rocket",
                        "metadata": {"scale": "growing_application"},
                    },
                    {
                        "id": "enterprise",
                        "label": "Enterprise Scale",
                        "description": "Large dataset, high throughput, mission-critical",
                        "icon": "building",
                        "metadata": {"scale": "enterprise"},
                    },
                ],
            },
            "budget": {
                "question": "What budget profile should I optimize for?",
                "options": [
                    {
                        "id": "low",
                        "label": "Startup Budget",
                        "description": "Prioritize open-source and low monthly cost",
                        "icon": "coin",
                        "metadata": {"budget": "low"},
                    },
                    {
                        "id": "medium",
                        "label": "Balanced Budget",
                        "description": "Mix managed reliability with cost control",
                        "icon": "scale",
                        "metadata": {"budget": "medium"},
                    },
                    {
                        "id": "high",
                        "label": "Performance First",
                        "description": "Prioritize reliability, speed, and operations",
                        "icon": "bolt",
                        "metadata": {"budget": "high"},
                    },
                ],
            },
            "implementation_preference": {
                "question": "What SDK or implementation style should I optimize for?",
                "options": [
                    {
                        "id": "python",
                        "label": "Python SDK",
                        "description": "Prioritize Python-native setup and examples",
                        "icon": "code",
                        "metadata": {
                            "implementation_preference": "python",
                            "implementation_language": "python",
                            "python_sdk": True,
                        },
                    },
                    {
                        "id": "typescript",
                        "label": "TypeScript / JavaScript SDK",
                        "description": "Prioritize Node.js and JS/TS examples",
                        "icon": "code",
                        "metadata": {
                            "implementation_preference": "typescript",
                            "implementation_language": "typescript",
                            "typescript_sdk": True,
                        },
                    },
                    {
                        "id": "api_only",
                        "label": "API-only / Language Neutral",
                        "description": "Prefer simple REST APIs and minimal SDK lock-in",
                        "icon": "document",
                        "metadata": {
                            "implementation_preference": "api_only",
                            "implementation_language": "api_only",
                        },
                    },
                    {
                        "id": "no_preference",
                        "label": "No Strong Preference",
                        "description": "Choose the best fit regardless of SDK language",
                        "icon": "split",
                        "metadata": {"implementation_preference": "no_preference"},
                    },
                ],
            },
            "hardware": {
                "question": "What hardware will this run on?",
                "options": [
                    {
                        "id": "cpu_only",
                        "label": "CPU-only machine",
                        "description": "Lowest cost, slower inference, smaller models",
                        "icon": "server",
                        "metadata": {"hardware": "cpu_only"},
                    },
                    {
                        "id": "consumer_gpu",
                        "label": "Consumer GPU",
                        "description": "NVIDIA/AMD GPU with 6GB+ VRAM",
                        "icon": "bolt",
                        "metadata": {"hardware": "consumer_gpu"},
                    },
                    {
                        "id": "apple_silicon",
                        "label": "Apple Silicon",
                        "description": "M1/M2/M3 Mac with unified memory",
                        "icon": "laptop",
                        "metadata": {"hardware": "apple_silicon"},
                    },
                    {
                        "id": "cloud_vm",
                        "label": "Low-cost cloud VM",
                        "description": "Small VPS or rented CPU/GPU instance",
                        "icon": "cloud",
                        "metadata": {"hardware": "cloud_vm"},
                    },
                ],
            },
            "agent_complexity": {
                "question": "What kind of agent workflow do you need?",
                "options": [
                    {
                        "id": "single_agent",
                        "label": "Single-agent task",
                        "description": "One assistant/tool loop, minimal orchestration",
                        "icon": "user",
                        "metadata": {"agent_complexity": "single_agent"},
                    },
                    {
                        "id": "multi_agent",
                        "label": "Multi-agent orchestration",
                        "description": "Planner, researcher, executor, reviewer roles",
                        "icon": "team",
                        "metadata": {"agent_complexity": "multi_agent"},
                    },
                ],
            },
            "deployment_preference": {
                "question": "Where can this run?",
                "options": [
                    {
                        "id": "managed",
                        "label": "Managed Cloud OK",
                        "description": "Vendor-hosted service is acceptable",
                        "icon": "cloud",
                        "metadata": {"deployment_preference": "managed"},
                    },
                    {
                        "id": "self_hosted",
                        "label": "Self-Hosted Preferred",
                        "description": "Run it in your own infrastructure",
                        "icon": "tools",
                        "metadata": {"deployment_preference": "self_hosted"},
                    },
                    {
                        "id": "hybrid",
                        "label": "Hybrid / Flexible",
                        "description": "Managed or self-hosted can both work",
                        "icon": "split",
                        "metadata": {"deployment_preference": "hybrid"},
                    },
                ],
            },
            "quality_priority": {
                "question": "What matters most for this choice?",
                "options": [
                    {
                        "id": "reasoning",
                        "label": "Reasoning Quality",
                        "description": "Prefer stronger answers and complex reasoning",
                        "icon": "brain",
                        "metadata": {"quality_priority": "reasoning"},
                    },
                    {
                        "id": "low_latency",
                        "label": "Low Latency",
                        "description": "Prefer fast responses and lower wait time",
                        "icon": "bolt",
                        "metadata": {"quality_priority": "low_latency"},
                    },
                    {
                        "id": "cost_efficiency",
                        "label": "Cost Efficiency",
                        "description": "Prefer lower ongoing usage cost",
                        "icon": "coin",
                        "metadata": {"quality_priority": "cost_efficiency"},
                    },
                ],
            },
        }

    async def _vector_db_comparison_events(
        self,
        task: dict,
        state: ConstraintState,
        client_context: dict | None,
    ) -> list[str] | None:
        """Phase-2 pipeline: retrieve → filter → score → shortlist → comparison panel."""
        playbook = get_playbook("vector_db_comparison") or {}
        retrieval = playbook.get("retrieval_config") or {}
        limit = int(retrieval.get("finalist_limit_default", 4))
        if state.get("budget") == "low":
            limit = int(retrieval.get("finalist_limit_low_budget", 3))

        pipeline = VectorDbRecommendationPipeline(self.db)
        result = await pipeline.run(state, finalist_limit=limit)
        trace = result.trace

        if client_context is not None:
            client_context["advisor_trace"] = trace.model_dump(mode="json")
            client_context["recommendation_explain"] = trace.to_explain_payload()

        if result.extra.get("filter_exhausted"):
            from src.services.constraint_negotiation import build_negotiation_option_cards

            negotiation = build_negotiation_option_cards(state, trace)
            text = (
                "No vector databases satisfy all of your hard constraints together. "
                "This is a constraint conflict, not a missing catalog — pick which "
                "requirement to relax first and I will re-run the comparison deterministically."
            )
            panel_command = {
                "action": "render",
                "panel": "option_cards",
                "title": "Constraint negotiation",
                "source": "planner",
                "data": negotiation,
            }
            return self._events(text, panel_command)

        slugs = result.shortlist
        if len(slugs) < 2:
            return self._text_only_events(
                "I could not build a meaningful comparison shortlist from the registry "
                "with your current constraints. Try relaxing budget or deployment filters."
            )

        comparison = await self.comparison_engine.compare(
            slugs=slugs,
            dimensions=COMPARISON_DIMENSIONS,
            weights=result.weights,
        )
        comparison_data = comparison.model_dump()
        comparison_data["recommendation"] = self._pipeline_recommendation(
            state,
            slugs,
            trace,
        )
        comparison_data["pipeline_scores"] = {r.slug: r.score for r in trace.scores}
        comparison_data["weights"] = result.weights
        comparison_data["shortlist"] = slugs
        ui = playbook.get("ui_behavior") or {}
        panel_command = {
            "action": "render",
            "panel": ui.get("comparison_panel", "comparison_chart"),
            "title": f"{task['label'].title()} Comparison",
            "data": {
                "comparison": comparison_data,
                "chart_type": ui.get("chart_type", "decision_surface"),
            },
        }
        text = (
            "I retrieved vector database modules, applied hard filters from your constraints, "
            "scored survivors deterministically, and ranked the shortlist below. "
            f"Top pick: **{slugs[0]}**."
        )
        logger.info("vector_db_comparison trace=%s", trace.steps)
        return self._events(text, panel_command)

    async def _category_comparison_events_v2(
        self,
        message: str,
        task: dict,
        state: ConstraintState,
        client_context: dict | None,
    ) -> list[str] | None:
        category = task.get("category", "")
        playbook_id = task.get("playbook_id") or (
            "vector_db_comparison" if category == "vector_databases" else f"category_{category}"
        )
        if category == "vector_databases":
            return await self._vector_db_comparison_events(task, state, client_context)

        limit = 4

        comparison_layer = resolve_comparison_layer(
            category, message, state=state, client_context=client_context
        )
        if comparison_layer:
            apply_comparison_layer_to_state(state, category, comparison_layer)
            if client_context is not None:
                client_context["comparison_layer"] = comparison_layer
                client_context["constraint_state"] = state.model_dump(mode="json")

        pipeline = get_pipeline(self.db, playbook_id, category=category)
        if pipeline is None:
            return self._pipeline_unavailable_events(playbook_id, "category comparison")

        result = await pipeline.run(
            state,
            finalist_limit=limit,
            comparison_layer=comparison_layer,
        )
        attach_pipeline_context(client_context, result, playbook_id=playbook_id)
        slugs = result.shortlist
        if len(slugs) < 2:
            layer_hint = ""
            if comparison_layer:
                layer_hint = (
                    f" for **{get_layer_label(category, comparison_layer)}** "
                    f"(layer: `{comparison_layer}`)"
                )
            return self._text_only_events(
                "Not enough comparable candidates passed filters"
                f"{layer_hint}. "
                "Try narrowing your question to one abstraction layer — e.g. rerankers only, "
                "hybrid retrieval strategies only, or orchestration frameworks only."
            )

        comparison = await self.comparison_engine.compare(
            slugs=slugs,
            dimensions=COMPARISON_DIMENSIONS,
            weights=result.weights,
        )
        comparison_data = comparison.model_dump()
        comparison_data["recommendation"] = self._pipeline_recommendation(state, slugs, result.trace)
        comparison_data["pipeline_scores"] = {r.slug: r.score for r in result.trace.scores}
        comparison_data["weights"] = result.weights
        comparison_data["shortlist"] = slugs
        title_suffix = task["label"].title()
        if comparison_layer:
            title_suffix = get_layer_label(category, comparison_layer)
        panel_command = {
            "action": "render",
            "panel": "comparison_chart",
            "title": f"{title_suffix} Comparison",
            "data": {"comparison": comparison_data, "chart_type": "decision_surface"},
        }
        text = (
            f"I deterministically ranked **{category.replace('_', ' ')}** modules for your constraints. "
            f"Top pick: **{slugs[0]}**."
        )
        return self._events(text, panel_command)

    async def _maybe_workspace_action_events(
        self,
        message: str,
        client_context: dict | None,
        state: ConstraintState,
        *,
        user_id: uuid.UUID | None = None,
    ) -> list[str] | None:
        if not client_context:
            return None

        profile = dict(client_context.get("consulting_profile") or {})

        if client_context.get("pin_current_strategy"):
            panel = client_context.get("current_panel_data")
            if not isinstance(panel, dict):
                return self._text_only_events(
                    "Open an architecture blueprint before pinning a strategy."
                )
            title = str(panel.get("title") or "Architecture strategy")
            profile = pin_current_architecture(
                profile,
                title=title,
                panel_data=panel,
                constraint_snapshot=state.model_dump(mode="json"),
            )
            client_context["consulting_profile"] = profile
            count = len(get_pinned_strategies(profile))
            text = (
                f"**Pinned** — “{title}” is saved to your strategy workspace ({count} pinned). "
                "Select two pinned futures to compare operational paths."
            )
            if isinstance(panel, dict) and panel.get("nodes"):
                panel_data = dict(panel)
                consulting = dict(panel_data.get("architecture_consulting") or {})
                consulting["strategy_workspace"] = {
                    "pinned": get_pinned_strategies(profile),
                    "count": count,
                }
                panel_data["architecture_consulting"] = consulting
                cmd = {
                    "action": "render",
                    "panel": "interactive_architecture",
                    "title": panel_data.get("title") or title,
                    "data": panel_data,
                }
                return self._events(text, cmd)
            return self._text_only_events(text)

        compare_ids = client_context.get("compare_pin_ids")
        if isinstance(compare_ids, list) and len(compare_ids) >= 2:
            pins = [p for p in get_pinned_strategies(profile) if p.get("id") in compare_ids]
            if len(pins) >= 2:
                from src.services.strategic_consulting import build_multi_pin_strategy_overview

                pipeline = get_pipeline(self.db, "rag_pipeline_design")
                if pipeline:
                    overview = await build_multi_pin_strategy_overview(
                        self.db, pipeline, pins[:3], state
                    )
                    if overview:
                        panel = client_context.get("current_panel_data")
                        if isinstance(panel, dict):
                            panel_data = dict(panel)
                            panel_data["strategy_mode"] = "multi"
                            consulting = panel_data.get("architecture_consulting") or {}
                            consulting["multi_strategy_overview"] = overview
                            panel_data["architecture_consulting"] = consulting
                            cmd = {
                                "action": "render",
                                "panel": "interactive_architecture",
                                "title": overview.get("theme", "Strategy workspace"),
                                "data": panel_data,
                            }
                            text = (
                                "**Strategy workspace** — comparing pinned architecture futures. "
                                "Review operational posture, cost evolution, and organizational fit."
                            )
                            return self._events(text, cmd)

        lever = client_context.get("tradeoff_lever")
        if lever:
            trial = apply_tradeoff_lever(state, str(lever))
            if trial:
                from src.services.architecture_simulation import ArchitectureSimulationSpec

                meta = TRADEOFF_LEVERS.get(str(lever), {})
                spec = ArchitectureSimulationSpec(
                    scenario_id=f"tradeoff_{lever}",
                    label=meta.get("label", "Tradeoff exploration"),
                    slot_updates={},
                    user_message_excerpt=message[:200],
                )
                return await self._architecture_simulation_events_v2(
                    message, client_context, trial, spec, user_id=user_id
                )

        posture_id = client_context.get("sandbox_posture")
        if posture_id:
            posture = next((p for p in SANDBOX_POSTURES if p["id"] == posture_id), None)
            if posture:
                from src.schemas.constraint_state import ConstraintSource
                from src.services.architecture_simulation import ArchitectureSimulationSpec

                trial = state.model_copy(deep=True)
                for key, value in posture["slots"].items():
                    trial.set_slot(
                        key,
                        value,
                        source=ConstraintSource.EXPLICIT,
                        confidence=1.0,
                        force=True,
                    )
                spec = ArchitectureSimulationSpec(
                    scenario_id=f"posture_{posture_id}",
                    label=posture["label"],
                    slot_updates={},
                    user_message_excerpt=message[:200],
                )
                return await self._architecture_simulation_events_v2(
                    message, client_context, trial, spec, user_id=user_id
                )

        return None

    async def _maybe_strategy_branch_events(
        self,
        message: str,
        client_context: dict | None,
        state: ConstraintState,
        *,
        user_id: uuid.UUID | None = None,
    ) -> list[str] | None:
        if not client_context:
            return None
        branch_id = client_context.get("strategy_branch_id")
        if not branch_id:
            from src.services.strategic_consulting import detect_strategy_branch_from_message

            branch_id = detect_strategy_branch_from_message(message)
            if branch_id:
                client_context["strategy_branch_id"] = branch_id
        if not branch_id:
            return None
        trial = apply_branch_slots(state, str(branch_id))
        if trial is None:
            return None
        from src.services.architecture_simulation import ArchitectureSimulationSpec

        spec = ArchitectureSimulationSpec(
            scenario_id=f"branch_{branch_id}",
            label=f"Strategy branch: {branch_id.replace('_', ' ')}",
            slot_updates={},
            user_message_excerpt=message[:200],
        )
        return await self._architecture_simulation_events_v2(
            message,
            client_context,
            trial,
            spec,
            user_id=user_id,
        )

    async def _maybe_dual_strategy_events(
        self,
        message: str,
        client_context: dict | None,
        state: ConstraintState,
        *,
        user_id: uuid.UUID | None = None,
    ) -> list[str] | None:
        spec = detect_dual_strategy_request(message)
        if not spec:
            return None
        pipeline = get_pipeline(self.db, "rag_pipeline_design")
        if pipeline is None:
            return None
        comparison = await build_dual_strategy_comparison(
            self.db, pipeline, state, spec, playbook_id="rag_pipeline_design"
        )
        if not comparison:
            return None

        primary = comparison["left_architecture"]
        panel_data = {
            "nodes": primary.get("nodes") or [],
            "edges": primary.get("edges") or [],
            "title": comparison["theme"],
            "selections": primary.get("selections") or {},
            "strategy_mode": "dual",
        }
        evolution_history = None
        if user_id:
            evolution_history = await list_evolution_history(self.db, user_id, limit=8)
        consulting = dict(primary.get("architecture_consulting") or {})
        consulting = enrich_architecture_consulting(
            consulting,
            state=state,
            trace=comparison.get("left_trace"),
            selections=primary.get("selections") or {},
            consulting_profile=(
                client_context.get("consulting_profile") if client_context else None
            ),
            evolution_history=evolution_history,
            strategy_comparison=comparison,
        )
        panel_data["architecture_consulting"] = consulting
        if user_id:
            await self._persist_evolution_snapshot(
                user_id,
                client_context,
                panel_data,
                state,
                transition_reason=f"Dual strategy: {comparison['theme']}",
            )
        if client_context is not None:
            client_context["strategy_comparison"] = comparison

        panel_command = {
            "action": "render",
            "panel": "interactive_architecture",
            "title": comparison["theme"],
            "data": panel_data,
        }
        text = (
            f"**Strategic architecture comparison** — {comparison['theme']}. "
            f"{comparison.get('consulting_summary', '')} "
            "Review operational posture, scaling, and long-term complexity side by side."
        )
        return self._events(text, panel_command)

    async def _maybe_architecture_simulation_events(
        self,
        message: str,
        client_context: dict | None,
        state: ConstraintState,
        *,
        intent_result: IntentResult | None = None,
        user_id: uuid.UUID | None = None,
    ) -> list[str] | None:
        if not client_context:
            return None
        on_architecture = client_context.get("current_panel") == "interactive_architecture"
        sim_intent = bool(
            intent_result
            and (intent_result.intent_id or "").startswith("architecture_simulation:")
        )
        if not on_architecture and not sim_intent:
            return None
        spec = detect_architecture_simulation(message, intent_result)
        if not spec:
            return None
        return await self._architecture_simulation_events_v2(
            message, client_context, state, spec, user_id=user_id
        )

    async def _architecture_simulation_events_v2(
        self,
        message: str,
        client_context: dict | None,
        state: ConstraintState,
        spec,
        *,
        user_id: uuid.UUID | None = None,
    ) -> list[str] | None:
        pipeline = get_pipeline(self.db, "rag_pipeline_design")
        if pipeline is None:
            return self._pipeline_unavailable_events("rag_pipeline_design", "architecture simulation")

        trial_state = apply_simulation_to_state(state, spec)
        if client_context is not None:
            client_context["constraint_state"] = trial_state.model_dump(mode="json")

        baseline_panel: dict[str, Any] = {}
        if isinstance(client_context.get("current_panel_data"), dict):
            baseline_panel = dict(client_context["current_panel_data"])

        result = await pipeline.run(trial_state)
        attach_pipeline_context(client_context, result, playbook_id="rag_pipeline_design")
        extra = result.extra or {}
        nodes = extra.get("nodes") or []
        edges = extra.get("edges") or []
        if not nodes:
            return self._text_only_events(
                "I could not simulate that scenario — no pipeline stages resolved. "
                "Try refining constraints or asking about a specific layer."
            )

        panel_data = {
            "nodes": nodes,
            "edges": edges,
            "title": f"Simulated: {spec.label}",
            "selections": extra.get("selections") or {},
            "comparison_baseline": {
                "title": baseline_panel.get("title") or "Current architecture",
                "nodes": baseline_panel.get("nodes") or [],
                "edges": baseline_panel.get("edges") or [],
                "selections": baseline_panel.get("selections") or {},
            },
        }
        panel_data = await self._attach_architecture_consulting(
            panel_data,
            trace=result.trace,
            state=trial_state,
            playbook_id="rag_pipeline_design",
            stage_decisions=extra.get("stage_decisions"),
            client_context=client_context,
            simulation_active=True,
            user_id=user_id,
        )
        consulting = panel_data.get("architecture_consulting") or {}
        replacements = (consulting.get("evolution") or {}).get("replacements") or []
        consulting["simulation"] = {
            "scenario_id": spec.scenario_id,
            "label": spec.label,
            "slot_updates": spec.slot_updates,
            "narrative": build_simulation_narrative(spec, replacements),
        }
        from src.services.phase6_intelligence import build_simulation_reasoning

        consulting["simulation_reasoning"] = build_simulation_reasoning(
            spec.label,
            trial_state,
            replacements,
            selections=extra.get("selections") or {},
        )
        panel_data["architecture_consulting"] = consulting

        panel_command = {
            "action": "render",
            "panel": "interactive_architecture",
            "title": panel_data["title"],
            "data": panel_data,
        }
        text = (
            f"**Architecture simulation** — {spec.label}. "
            "The blueprint shows your updated stack; compare against the prior architecture below. "
            f"{consulting['simulation']['narrative']}"
        )
        return self._events(text, panel_command)

    async def _rag_pipeline_events_v2(
        self,
        task: dict,
        state: ConstraintState,
        client_context: dict | None,
        *,
        user_id: uuid.UUID | None = None,
    ) -> list[str] | None:
        pipeline = get_pipeline(self.db, "rag_pipeline_design")
        if pipeline is None:
            return self._pipeline_unavailable_events("rag_pipeline_design", "RAG architecture")

        result = await pipeline.run(state)
        attach_pipeline_context(client_context, result, playbook_id="rag_pipeline_design")
        extra = result.extra or {}
        nodes = extra.get("nodes") or []
        edges = extra.get("edges") or []
        if not nodes:
            return None

        panel_data = {
            "nodes": nodes,
            "edges": edges,
            "title": "Recommended RAG Architecture",
            "selections": extra.get("selections") or {},
        }
        panel_data = await self._attach_architecture_consulting(
            panel_data,
            trace=result.trace,
            state=state,
            playbook_id="rag_pipeline_design",
            stage_decisions=extra.get("stage_decisions"),
            client_context=client_context,
            user_id=user_id,
        )
        panel_command = {
            "action": "render",
            "panel": "interactive_architecture",
            "title": "Recommended RAG Architecture",
            "data": panel_data,
        }
        text = (
            "I retrieved modules per RAG stage, filtered and scored each layer, and assembled "
            "this deterministic stack from your constraints."
        )
        return self._events(text, panel_command)

    async def _module_code_events_v2(
        self,
        message: str,
        client_context: dict | None,
        state: ConstraintState,
    ) -> list[str] | None:
        from src.services.pipelines.module_code import ModuleCodePipeline

        focus = None
        if client_context:
            focus = client_context.get("focus_module_slug")
            node = client_context.get("architecture_node")
            if isinstance(node, dict) and node.get("slug"):
                focus = str(node["slug"])

        pipeline = ModuleCodePipeline(self.db)
        result = await pipeline.run(state, message=message, focus_slug=str(focus) if focus else None)
        attach_pipeline_context(client_context, result, playbook_id="module_code")
        module = (result.extra or {}).get("module")
        if not module:
            return self._text_only_events(
                "I could not match that component to a module in the registry. "
                "Click **Show code** on an architecture node or name the module explicitly."
            )

        constraints = state.slot_values()
        example = self._pick_code_example(module, constraints)
        if not example:
            return self._text_only_events(f"No code example stored for **{module.name}** yet.")

        code_payload = {
            "title": example.get("title", module.name),
            "language": example.get("language", "python"),
            "code": example.get("code", ""),
            "filename": f"{module.slug}.{example.get('language', 'py')}",
            "moduleName": module.name,
        }
        on_architecture = (
            client_context
            and client_context.get("current_panel") == "interactive_architecture"
        )
        if on_architecture:
            panel_command = {
                "action": "update",
                "panel": "interactive_architecture",
                "title": f"{module.name} — Integration",
                "data": {"codeDrawer": code_payload},
            }
        else:
            panel_command = {
                "action": "render",
                "panel": "code_preview",
                "title": f"{module.name} — Integration",
                "data": code_payload,
            }
        text = f"Registry-backed integration code for **{module.name}** (deterministic module match)."
        return self._events(text, panel_command)

    async def _architecture_review_events_v2(
        self,
        client_context: dict | None,
        state: ConstraintState,
    ) -> list[str] | None:
        from src.services.pipelines.architecture_review import ArchitectureReviewPipeline

        panel_data = {}
        if client_context and isinstance(client_context.get("current_panel_data"), dict):
            panel_data = client_context["current_panel_data"]

        pipeline = ArchitectureReviewPipeline(self.db)
        result = await pipeline.run(state, panel_data=panel_data)
        attach_pipeline_context(client_context, result, playbook_id="architecture_review")
        findings = (result.extra or {}).get("findings") or []
        corrected = self._corrected_rag_architecture()
        findings_text = "\n".join(f"- {f['severity']}: {f['message']}" for f in findings)
        text = (
            "Deterministic architecture review complete. The panel shows a corrected reference stack.\n\n"
            f"{findings_text}"
        )
        panel_data = await self._attach_architecture_consulting(
            dict(corrected),
            trace=result.trace,
            state=state,
            playbook_id="architecture_review",
            client_context=client_context,
        )
        panel_command = {
            "action": "render",
            "panel": "interactive_architecture",
            "title": "Corrected RAG Architecture",
            "data": panel_data,
        }
        return self._events(text, panel_command)

    async def _local_ai_stack_events_v2(
        self,
        state: ConstraintState,
        client_context: dict | None,
    ) -> list[str] | None:
        pipeline = get_pipeline(self.db, "local_ai_stack")
        if pipeline is None:
            return self._pipeline_unavailable_events("local_ai_stack", "local AI stack")

        result = await pipeline.run(state)
        attach_pipeline_context(client_context, result, playbook_id="local_ai_stack")
        extra = result.extra or {}
        panel_data = {
            "title": "Lowest-Cost Private LLM Agent Stack",
            "nodes": extra.get("nodes") or [],
            "edges": extra.get("edges") or [],
        }
        panel_data = await self._attach_architecture_consulting(
            panel_data,
            trace=result.trace,
            state=state,
            playbook_id="local_ai_stack",
            client_context=client_context,
        )
        panel_command = {
            "action": "render",
            "panel": "interactive_architecture",
            "title": "Lowest-Cost Private LLM Agent Stack",
            "data": panel_data,
        }
        text = (
            "Deterministic local LLM + agent stack for your hardware and complexity constraints."
        )
        return self._events(text, panel_command)

    async def _attach_architecture_consulting(
        self,
        panel_data: dict,
        *,
        trace,
        state: ConstraintState,
        playbook_id: str,
        stage_decisions: dict | None = None,
        client_context: dict | None = None,
        simulation_active: bool = False,
        strategy_comparison: dict | None = None,
        user_id: uuid.UUID | None = None,
    ) -> dict:
        previous_panel_data = None
        previous_snapshot = None
        if client_context and isinstance(client_context.get("current_panel_data"), dict):
            previous_panel_data = client_context["current_panel_data"]
            prior = previous_panel_data.get("architecture_consulting") or {}
            previous_snapshot = prior.get("constraint_snapshot")

        selections = panel_data.get("selections")
        if not selections and stage_decisions:
            selections = {
                cat: detail.get("selected_slug")
                for cat, detail in stage_decisions.items()
                if isinstance(detail, dict) and detail.get("selected_slug")
            }

        from src.schemas.advisor_trace import AdvisorTrace

        effective_trace = trace or AdvisorTrace(
            playbook_id=playbook_id,
            constraint_snapshot=state.slot_values(),
        )

        consulting = build_architecture_consulting(
            trace=effective_trace,
            state=state,
            playbook_id=playbook_id,
            selections=selections,
            stage_decisions=stage_decisions,
            previous_snapshot=previous_snapshot,
            previous_panel_data=previous_panel_data,
            current_nodes=panel_data.get("nodes"),
        )

        evolution_history = None
        if user_id:
            evolution_history = await list_evolution_history(self.db, user_id, limit=8)

        consulting = enrich_architecture_consulting(
            consulting,
            state=state,
            trace=effective_trace,
            selections=selections or {},
            simulation_active=simulation_active,
            consulting_profile=(
                client_context.get("consulting_profile") if client_context else None
            ),
            evolution_history=evolution_history,
            strategy_comparison=strategy_comparison,
        )
        panel_data["architecture_consulting"] = consulting
        if selections:
            panel_data["selections"] = selections

        if user_id and not strategy_comparison:
            reason = None
            evolution = (consulting or {}).get("evolution") or {}
            if simulation_active:
                reason = "Scenario simulation"
            elif evolution.get("replacements"):
                reason = evolution.get("summary")
            await self._persist_evolution_snapshot(
                user_id,
                client_context,
                panel_data,
                state,
                transition_reason=reason,
            )
        return panel_data

    async def _persist_evolution_snapshot(
        self,
        user_id: uuid.UUID,
        client_context: dict | None,
        panel_data: dict,
        state: ConstraintState,
        *,
        transition_reason: str | None = None,
    ) -> None:
        conv_id = None
        if client_context and client_context.get("session_id"):
            try:
                conv_id = uuid.UUID(str(client_context["session_id"]))
            except ValueError:
                conv_id = None
        consulting = panel_data.get("architecture_consulting") or {}
        evolution = consulting.get("evolution") or {}
        await record_evolution_snapshot(
            self.db,
            user_id=user_id,
            conversation_id=conv_id,
            title=str(panel_data.get("title") or "Architecture")[:300],
            summary=evolution.get("summary") or consulting.get("continuity_framing"),
            selections=panel_data.get("selections") or {},
            nodes=panel_data.get("nodes") or [],
            constraint_snapshot=state.model_dump(mode="json"),
            transition_reason=(transition_reason or "")[:500] or None,
        )

    def _pipeline_recommendation(
        self,
        state: ConstraintState,
        shortlist: list[str],
        trace,
    ) -> str:
        top = shortlist[0] if shortlist else "the top option"
        parts = []
        if state.get("budget"):
            parts.append(f"{state.get('budget')} budget")
        if state.get("deployment_preference"):
            parts.append(str(state.get("deployment_preference")).replace("_", " "))
        if state.get("scale"):
            parts.append(str(state.get("scale")).replace("_", " "))
        constraint_text = " + ".join(parts) if parts else "your constraints"

        filter_note = ""
        if trace.filtered_out:
            names = ", ".join(f.slug for f in trace.filtered_out[:3])
            filter_note = f" Filtered out: {names}."

        score_note = ""
        top_score = next((r for r in trace.scores if r.slug == top), None)
        if top_score:
            score_note = f" Pipeline score {top_score.score:.2f}."

        return (
            f"Given {constraint_text}, **{top}** leads the deterministic shortlist."
            f"{filter_note}{score_note}"
        )

    def _pipeline_unavailable_events(self, playbook_id: str, label: str) -> list[str]:
        logger.error("pipeline unavailable playbook_id=%s", playbook_id)
        return self._text_only_events(
            f"The deterministic **{label}** engine is unavailable. "
            "Please retry or contact support — rankings are not shown without pipeline evidence."
        )

    def _is_module_code_request(self, combined: str, client_context: dict | None) -> bool:
        lower = combined.lower()
        code_patterns = (
            "show me integration code",
            "show integration code",
            "integration code for",
            "show code for",
            "code for",
            "code example",
            "sample code",
            "example code",
            "how to integrate",
        )
        if not any(pattern in lower for pattern in code_patterns) and "show code" not in lower:
            return False

        if any(
            phrase in lower
            for phrase in (
                "build a rag",
                "design a rag",
                "create a rag pipeline",
                "help me build a rag",
            )
        ) and "code for" not in lower and "integration code" not in lower:
            return False

        if not client_context:
            return False

        if client_context.get("focus_module_slug") or client_context.get("architecture_node"):
            return True
        if client_context.get("current_panel") == "interactive_architecture":
            return True
        serialized = client_context.get("constraint_state")
        if isinstance(serialized, dict):
            try:
                rag_state = ConstraintState.model_validate(serialized)
                if self._rag_constraints_complete(rag_state):
                    return True
            except Exception:
                pass
        active = str(client_context.get("active_task") or "").lower()
        return "rag" in active and any(
            term in lower for term in ("code", "integration", "example", "snippet")
        )

    def _rag_constraints_complete(self, state: ConstraintState) -> bool:
        return all(state.has(key) for key in ("scale", "budget", "implementation_preference"))

    async def _resolve_module_slug_for_code(
        self,
        message: str,
        client_context: dict | None,
    ) -> str | None:
        if client_context:
            focus = client_context.get("focus_module_slug")
            if focus:
                return str(focus)

            node = client_context.get("architecture_node")
            if isinstance(node, dict) and node.get("slug"):
                return str(node["slug"])

            panel_data = client_context.get("current_panel_data")
            if isinstance(panel_data, dict):
                for raw_node in panel_data.get("nodes") or []:
                    if not isinstance(raw_node, dict):
                        continue
                    label = str(raw_node.get("label") or "")
                    slug = raw_node.get("slug")
                    if label and label.lower() in message.lower() and slug:
                        return str(slug)

        match = re.search(
            r"(?:integration code for|code for|show (?:me )?(?:integration )?code for)\s+(.+?)(?:[.?]|$)",
            message,
            re.IGNORECASE,
        )
        query = match.group(1).strip() if match else message.strip()
        if not query:
            return None

        slug_guess = query.lower().replace(" ", "_").replace("-", "_")
        module = await self.module_service.get_by_slug(slug_guess)
        if module:
            return module.slug

        modules, _ = await self.module_service.list_modules(search=query, per_page=10)
        if not modules:
            return None

        query_lower = query.lower()
        for candidate in modules:
            if candidate.name.lower() == query_lower:
                return candidate.slug
        return modules[0].slug

    def _pick_code_example(self, module: Module, constraints: dict) -> dict | None:
        examples = module.code_examples or []
        if not examples:
            return None

        pref = constraints.get("implementation_preference")
        if pref == "python":
            for example in examples:
                if example.get("language") == "python":
                    return example
        if pref == "typescript":
            for example in examples:
                if example.get("language") in ("typescript", "javascript"):
                    return example
        return examples[0]

    def _review_rag_architecture(self, panel_data: dict) -> list[dict[str, str]]:
        nodes = panel_data.get("nodes") if isinstance(panel_data, dict) else []
        node_text = " ".join(
            " ".join(
                str(node.get(key, ""))
                for key in ("id", "label", "category", "slug", "module_slug", "description")
            )
            for node in nodes
            if isinstance(node, dict)
        ).lower()

        checks = [
            ("critical", "Missing user query entry point.", ("user", "query")),
            ("critical", "Missing reranker between retrieval and generation.", ("rerank", "cohere")),
            ("critical", "Missing prompt/context assembly before the LLM.", ("context", "prompt")),
            ("important", "Missing final answer node back to the user.", ("answer", "response")),
            ("important", "Missing evaluation or observability layer.", ("evaluation", "observability", "langfuse", "ragas")),
        ]
        findings = [
            {"severity": severity, "message": message}
            for severity, message, terms in checks
            if not any(term in node_text for term in terms)
        ]
        if not findings:
            findings.append({
                "severity": "minor",
                "message": "The core stages are present; the corrected panel makes data flow explicit.",
            })
        return findings

    def _corrected_rag_architecture(self) -> dict:
        nodes = [
            {
                "id": "documents",
                "label": "Documents",
                "category": "data_ingestion",
                "description": "source files",
            },
            {
                "id": "ingest",
                "label": "Unstructured OSS",
                "slug": "unstructured_oss",
                "category": "data_ingestion",
                "description": "parse docs",
            },
            {
                "id": "chunk",
                "label": "LlamaIndex Parsers",
                "slug": "llamaindex",
                "category": "chunking",
                "description": "chunk text",
            },
            {
                "id": "doc_embed",
                "label": "OpenAI Embeddings",
                "slug": "openai_embeddings",
                "category": "embeddings",
                "description": "embed chunks",
            },
            {
                "id": "store",
                "label": "Qdrant Cloud",
                "slug": "qdrant",
                "category": "vector_databases",
                "description": "store vectors",
            },
            {
                "id": "user_query",
                "label": "User Query",
                "category": "retrieval",
                "description": "question",
            },
            {
                "id": "query_embed",
                "label": "Query Embedding",
                "slug": "openai_embeddings",
                "category": "embeddings",
                "description": "embed query",
            },
            {
                "id": "retriever",
                "label": "Hybrid Search",
                "category": "retrieval",
                "description": "retrieve top-k",
            },
            {
                "id": "reranker",
                "label": "Cohere Rerank",
                "slug": "cohere_rerank",
                "category": "retrieval",
                "description": "rank context",
            },
            {
                "id": "context",
                "label": "Context Builder",
                "category": "rag_architectures",
                "description": "assemble prompt",
            },
            {
                "id": "llm",
                "label": "Claude 3.5 Haiku",
                "slug": "claude_3_5_haiku",
                "category": "llm_layer",
                "description": "generate",
            },
            {
                "id": "answer",
                "label": "Answer to User",
                "category": "rag_architectures",
                "description": "final response",
            },
            {
                "id": "observability",
                "label": "Langfuse / Ragas",
                "slug": "langfuse",
                "category": "evaluation",
                "description": "trace quality",
            },
        ]
        edges = [
            {"from": "documents", "to": "ingest", "label": "files"},
            {"from": "ingest", "to": "chunk", "label": "text"},
            {"from": "chunk", "to": "doc_embed", "label": "chunks"},
            {"from": "doc_embed", "to": "store", "label": "vectors"},
            {"from": "user_query", "to": "query_embed", "label": "query"},
            {"from": "query_embed", "to": "retriever", "label": "query vector"},
            {"from": "store", "to": "retriever", "label": "candidates"},
            {"from": "retriever", "to": "reranker", "label": "top-k"},
            {"from": "reranker", "to": "context", "label": "top chunks"},
            {"from": "context", "to": "llm", "label": "prompt"},
            {"from": "llm", "to": "answer", "label": "response"},
            {"from": "retriever", "to": "observability", "label": "trace"},
            {"from": "llm", "to": "observability", "label": "evaluate"},
        ]
        return {
            "title": "Corrected RAG Architecture",
            "nodes": nodes,
            "edges": edges,
        }

    def _required_constraints_for_category(self, category: str) -> list[str]:
        playbook_id = resolve_playbook_id(task_type="category_comparison", category=category)
        if playbook_id:
            slots = playbook_required_slots(playbook_id)
            if slots:
                return slots
        if category == "llm_layer":
            return ["quality_priority", "budget", "implementation_preference"]
        if category == "vector_databases":
            return ["budget", "scale", "deployment_preference"]
        if category == "agent_systems":
            return ["agent_complexity", "deployment_preference", "implementation_preference"]
        return ["scale", "budget", "implementation_preference"]

    def _detect_category(self, combined: str) -> str | None:
        for category, aliases in CATEGORY_ALIASES.items():
            if any(alias in combined for alias in aliases):
                return category
        return None

    def _short_node_description(self, module: Module) -> str:
        if module.pipeline_position:
            return module.pipeline_position.replace("_", " ")[:30]
        if module.tagline:
            return module.tagline[:30]
        return (module.category.slug if module.category else "component")[:30]

    def _option_card_events(self, task: dict, question: dict) -> list[str]:
        text = self._constraint_question_text(task, question["id"])
        panel_command = {
            "action": "render",
            "panel": "option_cards",
            "title": question["question"],
            "data": {
                "question_id": question["id"],
                "question": question["question"],
                "options": question["options"],
            },
        }
        return self._events(text, panel_command)

    def _constraint_question_text(self, task: dict, question_id: str) -> str:
        context = task["label"]
        messages = {
            "budget": f"I'll keep this focused on {context}. Budget is the hard filter, so let's set that first.",
            "scale": "Got it. Now I need scale so I can remove options that only fit prototypes or enterprise clusters.",
            "deployment_preference": "Good. One more constraint: where the data is allowed to live.",
            "implementation_preference": "Good. Now choose the implementation style so examples and tooling match your stack.",
            "hardware": "For a zero-cost local LLM stack, hardware is the binding constraint.",
            "agent_complexity": "Got it. Now choose whether this is a simple agent or multi-agent orchestration.",
            "quality_priority": f"I'll keep this focused on {context}. First, choose the quality priority that should drive the ranking.",
        }
        return messages.get(
            question_id,
            f"I'll keep this focused on {context}. I need one decision-critical constraint.",
        )

    def _text_only_events(self, text: str) -> list[str]:
        return [
            self.sse_event("text", {"content": text}),
            self.sse_event("done", {}),
        ]

    def _events(self, text: str, panel_command: dict) -> list[str]:
        panel_command = {**panel_command, "source": "planner"}
        return [
            self.sse_event("text", {"content": text}),
            self.sse_event("panel_command", {"command": panel_command}),
            self.sse_event("done", {}),
        ]

    def sse_event(self, event_type: str, data: dict) -> str:
        payload = {"type": event_type, **data}
        return f"data: {json.dumps(payload)}\n\n"
