"""Embedding + exemplar semantic intent layer (domain-scoped, planner-facing)."""

from __future__ import annotations

import asyncio
import logging
import math
from pathlib import Path
from typing import Any

import yaml

from src.advisor_playbooks.loader import resolve_playbook_id
from src.core.config import settings
from src.core.embeddings import generate_embedding, generate_embeddings_batch
from src.schemas.intent import IntentAlternative, IntentMatchEvidence, IntentResult

logger = logging.getLogger(__name__)

_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "advisor_intent" / "registry.yaml"

RAG_DESIGN_TERMS = (
    "rag",
    "retrieval augmented",
    "retrieval-augmented",
    "design",
    "designing",
    "build",
    "create",
    "end-to-end",
    "end to end",
    "pipeline",
    "from scratch",
    "ingestion",
    "chunking",
    "embedding",
)

MODULE_CODE_TERMS = (
    "show me integration code",
    "show integration code",
    "integration code for",
    "show code for",
    "code for",
    "code example",
    "sample code",
    "how to integrate",
    "show code",
)

REVIEW_TERMS = (
    "review",
    "reviewing",
    "check",
    "correct",
    "issue",
    "issues",
    "wrong",
    "fix",
    "what is wrong",
    "what should be added",
)

INTENT_LABELS: dict[str, str] = {
    "unknown": "general infrastructure advice",
    "ambiguous": "clarify the goal",
    "module_code": "integration code for a module",
    "architecture_review": "reviewing an architecture diagram",
    "local_ai_stack": "local / self-hosted LLM and agent stack",
    "rag_pipeline": "designing an end-to-end RAG pipeline",
    "category:vector_databases": "vector databases and similarity search",
    "category:embeddings": "embedding models and APIs",
    "category:chunking": "chunking and text splitting",
    "category:data_ingestion": "data ingestion and parsing",
    "category:retrieval": "retrieval and reranking",
    "category:llm_layer": "LLM choice and APIs",
    "category:agent_systems": "agent frameworks and orchestration",
    "category:evaluation": "evaluation and benchmarks",
    "category:deployment": "deployment and hosting",
}


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def _combined_text(message: str, client_context: dict | None) -> str:
    active = ""
    if client_context and client_context.get("active_task"):
        active = str(client_context["active_task"]).strip()
    return f"{active}\n{message}".strip() if active else message.strip()


def _explicit_intent_from_text(combined: str) -> str | None:
    """Keyword resolver for clear design-vs-review and short clarification replies."""
    text = combined.lower()

    if any(term in text for term in MODULE_CODE_TERMS):
        if not any(
            phrase in text
            for phrase in (
                "build a rag",
                "design a rag",
                "create a rag pipeline",
                "help me build a rag",
            )
        ) or "code for" in text or "integration code" in text:
            return "module_code"

    has_rag = any(term in text for term in RAG_DESIGN_TERMS)
    has_review = any(term in text for term in REVIEW_TERMS)
    mentions_diagram = "diagram" in text or "architecture diagram" in text

    if has_review and mentions_diagram and not has_rag:
        return "architecture_review"

    if has_rag and not has_review:
        strong_rag = any(
            term in text
            for term in (
                "rag",
                "retrieval augmented",
                "retrieval-augmented",
                "pipeline",
                "chunking",
                "end-to-end",
                "end to end",
            )
        )
        vector_retrieval = any(
            term in text
            for term in (
                "vector",
                "ann",
                "semantic retrieval",
                "similarity search",
                "nearest neighbor",
            )
        )
        if strong_rag and not vector_retrieval:
            return "rag_pipeline"

    if has_rag and has_review:
        if any(term in text for term in ("design", "designing", "build", "create", "pipeline")):
            return "rag_pipeline"
        if has_review and mentions_diagram:
            return "architecture_review"

    if any(term in text for term in ("designing", "design", "end to end", "end-to-end", "build")):
        return "rag_pipeline"

    if has_review and mentions_diagram:
        return "architecture_review"

    return None


def _resolved_intent_result(intent_id: str, *, confidence: float = 0.95) -> IntentResult:
    inferred: dict[str, Any] = {}
    if intent_id.startswith("category:"):
        inferred["category"] = intent_id.split(":", 1)[1]
    playbook_id = resolve_playbook_id(intent_id=intent_id)
    if playbook_id:
        inferred["playbook_id"] = playbook_id
    return IntentResult(
        intent_id=intent_id,
        confidence=confidence,
        margin=1.0,
        matched_evidence=[],
        inferred_parameters=inferred,
        needs_clarification=False,
        clarification_prompt=None,
        alternatives=[],
    )


def _should_use_resolved_intent(message: str, client_context: dict | None) -> str | None:
    """Reuse a prior clarification decision for short follow-ups in an active playbook."""
    if not client_context:
        return None
    resolved = client_context.get("resolved_intent_id")
    if not resolved or client_context.get("awaiting_intent_clarification"):
        return None
    combined = _combined_text(message, client_context)
    explicit = _explicit_intent_from_text(combined)
    if explicit:
        return None
    active_playbook = client_context.get("active_playbook_id")
    active_task = client_context.get("active_task")
    if active_playbook or active_task:
        return str(resolved)
    if len(message.strip()) < 150:
        return str(resolved)
    return None


def _load_registry() -> list[dict[str, Any]]:
    raw = yaml.safe_load(_REGISTRY_PATH.read_text(encoding="utf-8"))
    exemplars = raw.get("exemplars") or []
    out: list[dict[str, Any]] = []
    for row in exemplars:
        if not isinstance(row, dict):
            continue
        eid = row.get("id")
        iid = row.get("intent_id")
        text = row.get("text")
        if eid and iid and text:
            out.append({"id": str(eid), "intent_id": str(iid), "text": str(text)})
    return out


class SemanticIntentDetector:
    """Caches exemplar embeddings and scores user text against the intent registry."""

    def __init__(self) -> None:
        self._exemplars = _load_registry()
        self._vectors: list[list[float]] | None = None
        self._init_lock = asyncio.Lock()

    async def _ensure_vectors(self) -> None:
        if self._vectors is not None:
            return
        async with self._init_lock:
            if self._vectors is not None:
                return
            if not settings.embeddings_enabled or not self._exemplars:
                self._vectors = []
                return
            texts = [e["text"] for e in self._exemplars]
            batch = await generate_embeddings_batch(texts)
            if batch is None or len(batch) != len(texts):
                self._vectors = []
                return
            self._vectors = batch

    def _skip_semantic(self, message: str, client_context: dict | None) -> bool:
        """Short option-card replies should not override accumulated planner context."""
        if not client_context:
            return False
        if not isinstance(client_context.get("option_answer"), dict):
            return False
        return len(message.strip()) < 120

    async def detect(self, message: str, client_context: dict | None) -> IntentResult:
        """Return structured intent; falls back to unknown when disabled or API unavailable."""
        combined = _combined_text(message, client_context)

        explicit = _explicit_intent_from_text(combined)
        if explicit:
            return _resolved_intent_result(explicit)

        resolved_reuse = _should_use_resolved_intent(message, client_context)
        if resolved_reuse:
            logger.info(
                "semantic intent reused resolved_intent_id=%s playbook=%s",
                resolved_reuse,
                (client_context or {}).get("active_playbook_id"),
            )
            return _resolved_intent_result(resolved_reuse)

        if client_context and client_context.get("awaiting_intent_clarification"):
            explicit = _explicit_intent_from_text(combined)
            if explicit:
                return _resolved_intent_result(explicit)

        if not settings.semantic_intent_enabled or self._skip_semantic(message, client_context):
            return IntentResult(
                intent_id="unknown",
                confidence=0.0,
                margin=None,
                matched_evidence=[],
                inferred_parameters={},
                needs_clarification=False,
                clarification_prompt=None,
                alternatives=[],
            )

        query_text = combined

        await self._ensure_vectors()
        if not settings.embeddings_enabled or not self._exemplars or not self._vectors:
            return IntentResult(
                intent_id="unknown",
                confidence=0.0,
                margin=None,
                matched_evidence=[],
                inferred_parameters={},
                needs_clarification=False,
                clarification_prompt=None,
                alternatives=[],
            )

        query_emb = await generate_embedding(query_text)
        if query_emb is None:
            return IntentResult(
                intent_id="unknown",
                confidence=0.0,
                margin=None,
                matched_evidence=[],
                inferred_parameters={},
                needs_clarification=False,
                clarification_prompt=None,
                alternatives=[],
            )

        per_exemplar: list[tuple[dict[str, Any], float]] = []
        for ex, vec in zip(self._exemplars, self._vectors, strict=False):
            sim = _cosine_similarity(query_emb, vec)
            per_exemplar.append((ex, sim))

        per_exemplar.sort(key=lambda x: x[1], reverse=True)

        intent_best: dict[str, float] = {}
        for ex, sim in per_exemplar:
            iid = ex["intent_id"]
            intent_best[iid] = max(intent_best.get(iid, 0.0), sim)

        ranked = sorted(intent_best.items(), key=lambda x: (-x[1], x[0]))
        best_id, best_score = ranked[0]
        second_score = ranked[1][1] if len(ranked) > 1 else 0.0
        margin = best_score - second_score

        evidence = [
            IntentMatchEvidence(
                exemplar_id=ex["id"],
                exemplar_text=ex["text"],
                intent_id=ex["intent_id"],
                similarity=round(sim, 4),
            )
            for ex, sim in per_exemplar[:3]
        ]

        alternatives = [
            IntentAlternative(intent_id=iid, score=round(score, 4))
            for iid, score in ranked[1:4]
        ]

        inferred: dict[str, Any] = {}
        if best_id.startswith("category:"):
            inferred["category"] = best_id.split(":", 1)[1]

        min_conf = settings.semantic_intent_min_confidence
        clarify_low = settings.semantic_intent_clarify_low
        clarify_m = settings.semantic_intent_clarify_margin

        ambiguous_tie = len(ranked) >= 2 and margin < clarify_m and best_score >= min_conf * 0.9
        ambiguous_band = (
            best_score >= min_conf * 0.85
            and best_score < clarify_low
            and margin < clarify_m
        )

        if ambiguous_tie or ambiguous_band:
            if client_context and client_context.get("resolved_intent_id"):
                logger.info(
                    "semantic intent skip reclarification resolved=%s",
                    client_context.get("resolved_intent_id"),
                )
                return _resolved_intent_result(str(client_context["resolved_intent_id"]))
            prompt = self._clarification_prompt(ranked[:2])
            logger.info(
                "semantic intent clarification best=%s margin=%.4f score=%.4f",
                best_id,
                margin,
                best_score,
            )
            return IntentResult(
                intent_id="ambiguous",
                confidence=round(best_score, 4),
                margin=round(margin, 4),
                matched_evidence=evidence,
                inferred_parameters=inferred,
                needs_clarification=True,
                clarification_prompt=prompt,
                alternatives=alternatives,
            )

        if best_score < min_conf:
            return IntentResult(
                intent_id="unknown",
                confidence=round(best_score, 4),
                margin=round(margin, 4) if ranked else None,
                matched_evidence=evidence,
                inferred_parameters={},
                needs_clarification=False,
                clarification_prompt=None,
                alternatives=alternatives,
            )

        playbook_id = resolve_playbook_id(intent_id=best_id)
        if playbook_id:
            inferred["playbook_id"] = playbook_id
        logger.info(
            "semantic intent resolved intent_id=%s confidence=%.4f margin=%s playbook=%s",
            best_id,
            best_score,
            round(margin, 4) if ranked else None,
            playbook_id,
        )
        return IntentResult(
            intent_id=best_id,
            confidence=round(best_score, 4),
            margin=round(margin, 4) if ranked else None,
            matched_evidence=evidence,
            inferred_parameters=inferred,
            needs_clarification=False,
            clarification_prompt=None,
            alternatives=alternatives,
        )

    def _clarification_prompt(self, top: list[tuple[str, float]]) -> str:
        if len(top) >= 2:
            a = INTENT_LABELS.get(top[0][0], top[0][0])
            b = INTENT_LABELS.get(top[1][0], top[1][0])
            return (
                "I am not fully sure which track you want. Should we focus on "
                f"**{a}** or **{b}**? Reply in one short sentence and I will continue."
            )
        return (
            "I am not fully sure which advisor flow to run. "
            "Mention **vector databases**, **RAG pipeline**, **agents**, or **architecture review** "
            "and I will lock onto that."
        )


_semantic_detector: SemanticIntentDetector | None = None


def get_semantic_intent_detector() -> SemanticIntentDetector:
    global _semantic_detector
    if _semantic_detector is None:
        _semantic_detector = SemanticIntentDetector()
    return _semantic_detector


def force_intent_result(intent_id: str) -> IntentResult:
    """Build a high-confidence intent result (e.g. after user picks a clarification chip)."""
    return _resolved_intent_result(intent_id)
