"""Build and merge ConstraintState from messages and UI context."""

from __future__ import annotations

import logging
import re
from typing import Any

from src.schemas.constraint_state import ConstraintSource, ConstraintState

logger = logging.getLogger(__name__)


class ConstraintStateService:
    """Canonical constraint extraction and merge logic."""

    @staticmethod
    def build(
        message: str,
        client_context: dict | None = None,
        *,
        playbook_id: str | None = None,
    ) -> ConstraintState:
        state = ConstraintState(playbook_id=playbook_id)
        combined = message.lower()

        if client_context:
            combined = f"{client_context.get('active_task', '')} {message}".lower()
            if client_context.get("active_playbook_id"):
                state.playbook_id = str(client_context["active_playbook_id"])

            serialized = client_context.get("constraint_state")
            if isinstance(serialized, dict):
                _hydrate_from_serialized(state, serialized)

            option_answer = client_context.get("option_answer")
            if isinstance(option_answer, dict):
                metadata = option_answer.get("metadata")
                if isinstance(metadata, dict):
                    state.merge_flat_slot_values(metadata, source=ConstraintSource.OPTION_CARD)
                qid = option_answer.get("question_id")
                aid = option_answer.get("answer_id")
                label = option_answer.get("answer_label")
                if qid and aid:
                    state.set_slot(
                        str(qid),
                        aid,
                        source=ConstraintSource.OPTION_CARD,
                        confidence=1.0,
                        raw_label=str(label) if label else None,
                        force=True,
                    )

        ConstraintStateService._infer_from_text(state, combined)
        return state

    @staticmethod
    def _infer_from_text(state: ConstraintState, combined: str) -> None:
        def infer(key: str, value: Any, confidence: float = 0.7) -> None:
            if not state.has(key):
                state.set_slot(key, value, source=ConstraintSource.INFERRED, confidence=confidence)

        if "python" in combined:
            infer("python_sdk", True, 0.85)
            infer("implementation_preference", "python", 0.85)
            infer("implementation_language", "python", 0.85)
        if "typescript" in combined or "javascript" in combined:
            infer("implementation_preference", "typescript", 0.85)
            infer("implementation_language", "typescript", 0.85)

        if re.search(r"\b(startup|cheap|low cost|low-cost|budget)\b", combined):
            infer("budget", "low", 0.8)
        elif re.search(r"\b(enterprise|unlimited|performance first)\b", combined):
            infer("budget", "high", 0.75)
        elif re.search(r"\bmoderate|balanced\b", combined):
            infer("budget", "medium", 0.7)

        if re.search(r"\b(prototype|demo|mvp)\b", combined):
            infer("scale", "prototype", 0.75)
        elif re.search(r"\b(enterprise|mission.critical|high throughput)\b", combined):
            infer("scale", "enterprise", 0.8)
        elif re.search(r"\b(growing|production)\b", combined):
            infer("scale", "growing_application", 0.75)

        if re.search(r"\b(self[- ]?host(?:ed)?|on[- ]?prem(?:ises)?|on prem|local deploy)\b", combined):
            infer("deployment_preference", "self_hosted", 0.85)
        elif re.search(r"\b(managed|saas|cloud only)\b", combined):
            infer("deployment_preference", "managed", 0.8)
        elif "hybrid" in combined:
            infer("deployment_preference", "hybrid", 0.75)

        if re.search(r"\b(persist|durability|disk)\b", combined):
            infer("persistence_required", True, 0.8)

        if re.search(r"\b(low latency|fast retrieval|sub.?second)\b", combined):
            infer("latency_priority", "high", 0.75)


def _hydrate_from_serialized(state: ConstraintState, payload: dict[str, Any]) -> None:
    from src.schemas.constraint_state import ConstraintSlot

    slots = payload.get("slots") or {}
    if not isinstance(slots, dict):
        return
    for key, raw in slots.items():
        if isinstance(raw, dict) and "value" in raw:
            state.slots[key] = ConstraintSlot.model_validate(raw)
        else:
            state.set_slot(key, raw, source=ConstraintSource.ACCUMULATED, confidence=0.9)
