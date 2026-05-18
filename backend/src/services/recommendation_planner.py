"""Deterministic planning layer for advisor recommendations."""

import json

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.module import Module
from src.modules.comparison_engine import ComparisonEngine
from src.services.module_service import ModuleService


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

    async def plan(self, message: str, client_context: dict | None) -> list[str] | None:
        task = self.detect_task(message, client_context)
        if not task:
            return None

        constraints = self.extract_constraints(message, client_context)
        if task["type"] == "architecture_review":
            return self._architecture_review_events(client_context)

        missing_question = self.next_missing_question(task, constraints)
        if missing_question:
            return self._option_card_events(task, missing_question)

        if task["type"] == "rag_pipeline":
            return await self._rag_pipeline_events(task, constraints)

        if task["type"] == "category_comparison":
            return await self._category_comparison_events(task, constraints)

        if task["type"] == "local_ai_stack":
            return self._local_ai_stack_events(constraints)

        return None

    def detect_task(self, message: str, client_context: dict | None) -> dict | None:
        active_task = ""
        if client_context:
            active_task = str(client_context.get("active_task") or "")

        combined = f"{active_task} {message}".lower()
        has_option_answer = bool(
            client_context and isinstance(client_context.get("option_answer"), dict)
        )

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

    def extract_constraints(
        self,
        message: str,
        client_context: dict | None,
    ) -> dict:
        constraints: dict = {}
        combined = message.lower()

        if client_context:
            combined = f"{client_context.get('active_task', '')} {message}".lower()
            option_answer = client_context.get("option_answer")
            if isinstance(option_answer, dict):
                metadata = option_answer.get("metadata")
                if isinstance(metadata, dict):
                    constraints.update(metadata)

                question_id = option_answer.get("question_id")
                answer_id = option_answer.get("answer_id")
                if question_id and answer_id:
                    constraints[str(question_id)] = answer_id

            accumulated = client_context.get("constraints")
            if isinstance(accumulated, dict):
                constraints.update(accumulated)

        if "python" in combined:
            constraints["python_sdk"] = True
            constraints.setdefault("implementation_preference", "python")
            constraints.setdefault("implementation_language", "python")
        if "typescript" in combined or "javascript" in combined:
            constraints.setdefault("implementation_preference", "typescript")
            constraints.setdefault("implementation_language", "typescript")
        if "api only" in combined or "rest api" in combined:
            constraints.setdefault("implementation_preference", "api_only")
            constraints.setdefault("implementation_language", "api_only")

        if "cpu" in combined or "cpu-only" in combined:
            constraints.setdefault("hardware", "cpu_only")
        if "consumer gpu" in combined or "rtx" in combined or "gpu" in combined:
            constraints.setdefault("hardware", "consumer_gpu")
        if (
            "apple silicon" in combined
            or "macbook" in combined
            or "m1" in combined
            or "m2" in combined
            or "m3" in combined
        ):
            constraints.setdefault("hardware", "apple_silicon")
        if "cloud vm" in combined or "vps" in combined:
            constraints.setdefault("hardware", "cloud_vm")

        if "single agent" in combined or "simple agent" in combined:
            constraints.setdefault("agent_complexity", "single_agent")
        if "multi-agent" in combined or "multi agent" in combined or "orchestration" in combined:
            constraints.setdefault("agent_complexity", "multi_agent")

        if "growing" in combined or "production" in combined:
            constraints.setdefault("scale", "growing_application")
        if "enterprise" in combined or "mission-critical" in combined:
            constraints["scale"] = "enterprise"
        if "prototype" in combined or "demo" in combined or "small" in combined:
            constraints.setdefault("scale", "prototype")

        if (
            "startup budget" in combined
            or "low budget" in combined
            or "under $50" in combined
            or "$50/mo" in combined
            or "lowest cost" in combined
            or "absolute lowest" in combined
        ):
            constraints["budget"] = "low"
        if "moderate cost" in combined or "balanced budget" in combined:
            constraints.setdefault("budget", "medium")
        if "performance first" in combined or "growth budget" in combined:
            constraints.setdefault("budget", "high")

        if "managed" in combined or "cloud" in combined:
            constraints.setdefault("deployment_preference", "managed")
        if "self-host" in combined or "on-prem" in combined or "private" in combined:
            constraints["deployment_preference"] = "self_hosted"

        if "reasoning" in combined:
            constraints.setdefault("quality_priority", "reasoning")
        if "low latency" in combined or "latency" in combined:
            constraints.setdefault("quality_priority", "low_latency")
        if "accuracy" in combined:
            constraints.setdefault("quality_priority", "accuracy")

        return constraints

    def next_missing_question(self, task: dict, constraints: dict) -> dict | None:
        questions = self.constraint_questions()
        for question_id in task["required_constraints"]:
            if constraints.get(question_id):
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

    async def _category_comparison_events(
        self,
        task: dict,
        constraints: dict,
    ) -> list[str] | None:
        slugs, weights = await self.rank_category_finalists(
            task["category"],
            constraints,
        )
        if len(slugs) < 2:
            return None

        comparison = await self.comparison_engine.compare(
            slugs=slugs,
            dimensions=COMPARISON_DIMENSIONS,
            weights=weights,
        )
        comparison_data = comparison.model_dump()
        comparison_data["recommendation"] = self._constraint_aware_recommendation(
            task,
            constraints,
            comparison_data["overall_ranking"],
        )
        panel_command = {
            "action": "render",
            "panel": "comparison_chart",
            "title": f"{task['label'].title()} Comparison",
            "data": {
                "comparison": comparison_data,
                "chart_type": "radar",
            },
        }
        text = (
            f"I filtered first, then ranked the {task['label']} finalists that match "
            "your constraints. The panel shows only viable options."
        )
        return self._events(text, panel_command)

    async def _rag_pipeline_events(
        self,
        task: dict,
        constraints: dict,
    ) -> list[str] | None:
        nodes = []
        edges = []
        selected = {}

        for category in RAG_PIPELINE:
            modules, _ = await self.module_service.list_modules(
                category=category,
                per_page=100,
            )
            if not modules:
                continue
            module = self.rank_modules(modules, constraints)[0]
            selected[category] = module
            nodes.append({
                "id": category,
                "label": module.name,
                "slug": module.slug,
                "category": category,
                "description": self._short_node_description(module),
            })

        for source, target in zip(RAG_PIPELINE, RAG_PIPELINE[1:], strict=False):
            if source in selected and target in selected:
                edges.append({"from": source, "to": target})

        if not nodes:
            return None

        panel_command = {
            "action": "render",
            "panel": "interactive_architecture",
            "title": "Recommended RAG Architecture",
            "data": {
                "nodes": nodes,
                "edges": edges,
                "title": "Recommended RAG Architecture",
            },
        }
        text = (
            "I have enough constraints now. Here is a deterministic RAG stack "
            "optimized for your scale, budget, and implementation preference."
        )
        return self._events(text, panel_command)

    def _architecture_review_events(self, client_context: dict | None) -> list[str]:
        panel_data = {}
        if client_context and isinstance(client_context.get("current_panel_data"), dict):
            panel_data = client_context["current_panel_data"]

        findings = self._review_rag_architecture(panel_data)
        corrected = self._corrected_rag_architecture()
        findings_text = "\n".join(
            f"- {finding['severity']}: {finding['message']}" for finding in findings
        )
        text = (
            "I found the main gaps and replaced the panel with a corrected interactive "
            "RAG architecture. Keep using the node hover menu for Learn more, Swap "
            f"component, and Show code.\n\n{findings_text}"
        )
        panel_command = {
            "action": "render",
            "panel": "interactive_architecture",
            "title": "Corrected RAG Architecture",
            "data": corrected,
        }
        return self._events(text, panel_command)

    def _local_ai_stack_events(self, constraints: dict) -> list[str]:
        agent_label = (
            "LangChain Agent"
            if constraints.get("agent_complexity") == "single_agent"
            else "CrewAI"
        )
        agent_slug = "langchain" if agent_label == "LangChain Agent" else "crewai"
        model_label = "Llama 3.2/3.3 8B"
        if constraints.get("hardware") == "cpu_only":
            model_label = "Llama 3.2 3B/8B"

        panel_command = {
            "action": "render",
            "panel": "interactive_architecture",
            "title": "Lowest-Cost Private LLM Agent Stack",
            "data": {
                "title": "Lowest-Cost Private LLM Agent Stack",
                "nodes": [
                    {
                        "id": "app",
                        "label": "Your App",
                        "category": "agent_systems",
                        "description": "user task",
                    },
                    {
                        "id": "agent",
                        "label": agent_label,
                        "slug": agent_slug,
                        "category": "agent_systems",
                        "description": "orchestrate tools",
                    },
                    {
                        "id": "ollama",
                        "label": "Ollama",
                        "slug": "ollama",
                        "category": "llm_layer",
                        "description": "local runtime",
                    },
                    {
                        "id": "model",
                        "label": model_label,
                        "category": "llm_layer",
                        "description": "open model",
                    },
                    {
                        "id": "tools",
                        "label": "Local Tools",
                        "category": "agent_systems",
                        "description": "private actions",
                    },
                ],
                "edges": [
                    {"from": "app", "to": "agent", "label": "task"},
                    {"from": "agent", "to": "ollama", "label": "chat API"},
                    {"from": "ollama", "to": "model", "label": "runs"},
                    {"from": "agent", "to": "tools", "label": "tool calls"},
                ],
            },
        }
        text = (
            "For lowest-cost + self-hosted privacy, start with a local architecture first. "
            "The panel shows the stack; ask for code after you confirm the shape."
        )
        return self._events(text, panel_command)

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

    async def rank_category_finalists(
        self,
        category: str,
        constraints: dict,
    ) -> tuple[list[str], dict[str, float]]:
        modules, _ = await self.module_service.list_modules(category=category, per_page=100)
        modules = self._apply_hard_filters(category, modules, constraints)
        ranked = self.rank_modules(modules, constraints)
        limit = 3 if category == "vector_databases" and constraints.get("budget") == "low" else 4
        return [module.slug for module in ranked[:limit]], self.weights_for_constraints(constraints)

    def _apply_hard_filters(
        self,
        category: str,
        modules: list[Module],
        constraints: dict,
    ) -> list[Module]:
        if category != "vector_databases":
            return modules

        excluded: set[str] = set()
        if constraints.get("budget") == "low":
            # Startup / under-$50 vector DB path: exclude options that need
            # higher managed tiers or non-trivial self-hosted clusters.
            excluded.update({"pinecone", "milvus"})

        if constraints.get("deployment_preference") == "self_hosted":
            excluded.update({"pinecone"})

        filtered = [module for module in modules if module.slug not in excluded]
        return filtered or modules

    def rank_modules(self, modules: list[Module], constraints: dict) -> list[Module]:
        weights = self.weights_for_constraints(constraints)

        def score(module: Module) -> float:
            scores = module.comparison_scores or {}
            total = 0.0
            total_weight = 0.0
            for dimension, weight in weights.items():
                dim_data = scores.get(dimension, {})
                raw_score = dim_data.get("score", 5) if isinstance(dim_data, dict) else 5
                total += raw_score * weight
                total_weight += weight

            total = total / total_weight if total_weight else 0
            pricing = module.pricing_model or ""
            text = " ".join([
                module.name,
                module.tagline or "",
                module.description or "",
                json.dumps(module.technical_specs or {}),
                json.dumps(module.supported_operations or []),
            ]).lower()

            if constraints.get("budget") == "low" and pricing in {"open_source", "free"}:
                total += 0.5
            if constraints.get("deployment_preference") == "self_hosted" and pricing == "open_source":
                total += 0.5
            if constraints.get("python_sdk") and "python" in text:
                total += 0.4
            if constraints.get("typescript_sdk") and any(term in text for term in ("typescript", "javascript", "node")):
                total += 0.4
            return total

        return sorted(modules, key=score, reverse=True)

    def weights_for_constraints(self, constraints: dict) -> dict[str, float]:
        weights = {
            "performance": 1.3,
            "scalability": 1.4,
            "ease_of_use": 1.2,
            "cost_efficiency": 1.0,
            "community": 1.0,
            "maturity": 1.1,
            "flexibility": 1.0,
            "data_privacy": 1.0,
        }

        scale = constraints.get("scale")
        if scale in {"growing_application", "enterprise"}:
            weights.update({"scalability": 2.5, "performance": 2.0, "maturity": 1.7})
        elif scale == "prototype":
            weights.update({"ease_of_use": 2.2, "cost_efficiency": 1.7})

        if constraints.get("budget") == "low":
            weights["cost_efficiency"] = 2.5
        elif constraints.get("budget") == "high":
            weights["performance"] = 2.2
            weights["maturity"] = 1.8

        if constraints.get("python_sdk") or constraints.get("typescript_sdk"):
            weights["ease_of_use"] = max(weights["ease_of_use"], 2.0)
            weights["community"] = 1.3

        if constraints.get("deployment_preference") == "self_hosted":
            weights["data_privacy"] = 2.4
            weights["flexibility"] = 1.8

        priority = constraints.get("quality_priority")
        if priority == "reasoning" or priority == "accuracy":
            weights["performance"] = max(weights["performance"], 2.5)
            weights["maturity"] = max(weights["maturity"], 1.8)
        elif priority == "low_latency":
            weights["performance"] = max(weights["performance"], 2.8)
            weights["cost_efficiency"] = max(weights["cost_efficiency"], 1.5)
        elif priority == "cost_efficiency":
            weights["cost_efficiency"] = max(weights["cost_efficiency"], 2.8)

        return weights

    def _constraint_aware_recommendation(
        self,
        task: dict,
        constraints: dict,
        overall_ranking: list[str],
    ) -> str:
        top = overall_ranking[0] if overall_ranking else "the top option"
        constraint_text = self._constraint_summary(constraints)
        reasons = []

        if constraints.get("budget") == "low":
            reasons.append("startup budget -> excluded candidates that exceed the low-cost path")
        if constraints.get("scale"):
            reasons.append(f"{constraints['scale']} scale -> weighted scalability and performance appropriately")
        if constraints.get("deployment_preference"):
            reasons.append(f"{constraints['deployment_preference']} hosting -> filtered by deployment fit")
        if constraints.get("quality_priority"):
            reasons.append(f"{constraints['quality_priority']} priority -> weighted the matching quality dimension")

        if not reasons:
            reasons.append("your stated constraints -> ranked only relevant finalists")

        alternative = overall_ranking[1] if len(overall_ranking) > 1 else "the runner-up"
        bullet_text = "\n".join(f"- {reason}" for reason in reasons[:2])
        return (
            f"Given your {constraint_text}, I recommend {top} because:\n"
            f"{bullet_text}\n\n"
            f"If that constraint changes, consider {alternative} instead."
        )

    def _constraint_summary(self, constraints: dict) -> str:
        parts = []
        if constraints.get("budget") == "low":
            parts.append("startup budget")
        elif constraints.get("budget"):
            parts.append(f"{constraints['budget']} budget")
        if constraints.get("scale"):
            parts.append(str(constraints["scale"]).replace("_", " "))
        if constraints.get("deployment_preference"):
            parts.append(str(constraints["deployment_preference"]).replace("_", " "))
        if constraints.get("implementation_preference"):
            parts.append(str(constraints["implementation_preference"]).replace("_", " "))
        if constraints.get("quality_priority"):
            parts.append(str(constraints["quality_priority"]).replace("_", " "))
        return " + ".join(parts) if parts else "constraints"

    def _required_constraints_for_category(self, category: str) -> list[str]:
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

    def _events(self, text: str, panel_command: dict) -> list[str]:
        return [
            self.sse_event("text", {"content": text}),
            self.sse_event("panel_command", {"command": panel_command}),
            self.sse_event("done", {}),
        ]

    def sse_event(self, event_type: str, data: dict) -> str:
        payload = {"type": event_type, **data}
        return f"data: {json.dumps(payload)}\n\n"
