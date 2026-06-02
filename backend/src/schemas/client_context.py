"""Allowlisted, deeply validated client_context for advisor chat."""



from __future__ import annotations



import json

import logging

from typing import Any



from pydantic import BaseModel, ConfigDict, Field, field_validator



from src.schemas.payload_sanitizer import (

    MAX_PROMPT_TOKEN_BUDGET_CHARS,

    SanitizationStats,

    estimate_prompt_chars,

    sanitize_nested,

)



logger = logging.getLogger(__name__)



MAX_CLIENT_CONTEXT_JSON_BYTES = 32_000

MAX_STRING = 2_000

MAX_TASK = 500

MAX_PANEL_DATA_BYTES = 12_000

MAX_CONSTRAINT_SLOTS = 48

MAX_COMPARE_PINS = 8





class OptionAnswerContext(BaseModel):

    model_config = ConfigDict(extra="forbid")



    question_id: str | None = Field(default=None, max_length=64)

    question: str | None = Field(default=None, max_length=MAX_STRING)

    answer_id: str | int | float | bool | None = None

    answer_label: str | None = Field(default=None, max_length=MAX_STRING)

    metadata: dict[str, Any] | None = None



    @field_validator("metadata", mode="before")

    @classmethod

    def sanitize_metadata(cls, value: Any) -> Any:

        if value is None:

            return None

        stats = SanitizationStats()

        return sanitize_nested(value, stats=stats)





class IntentClarificationChoice(BaseModel):

    model_config = ConfigDict(extra="forbid")



    intent_id: str = Field(max_length=128)

    label: str | None = Field(default=None, max_length=MAX_STRING)





class ArchitectureNodeRef(BaseModel):

    model_config = ConfigDict(extra="forbid")



    id: str | None = Field(default=None, max_length=128)

    label: str | None = Field(default=None, max_length=MAX_STRING)

    slug: str | None = Field(default=None, max_length=128)

    category: str | None = Field(default=None, max_length=64)





class ConstraintSlotPayload(BaseModel):

    model_config = ConfigDict(extra="forbid")



    value: str | int | float | bool | list[str]

    source: str = Field(max_length=32)

    confidence: float = Field(default=0.75, ge=0.0, le=1.0)

    raw_label: str | None = Field(default=None, max_length=MAX_STRING)





class ConstraintStatePayload(BaseModel):

    model_config = ConfigDict(extra="forbid")



    slots: dict[str, ConstraintSlotPayload] = Field(default_factory=dict)

    playbook_id: str | None = Field(default=None, max_length=128)

    version: str = Field(default="1", max_length=8)





class ValidatedClientContext(BaseModel):

    """Strict allowlist — unknown top-level fields are stripped before validation."""



    model_config = ConfigDict(extra="forbid")



    active_task: str | None = Field(default=None, max_length=MAX_TASK)

    active_playbook_id: str | None = Field(default=None, max_length=128)

    awaiting_intent_clarification: bool | None = None

    resolved_intent_id: str | None = Field(default=None, max_length=128)

    intent_alternatives: list[str] | None = None

    intent_alternative_labels: list[str] | None = None

    intent_clarification_choice: IntentClarificationChoice | None = None

    current_panel: str | None = Field(default=None, max_length=64)

    current_panel_data: dict[str, Any] | None = None

    constraint_state: ConstraintStatePayload | None = None

    option_answer: OptionAnswerContext | None = None

    focus_module_slug: str | None = Field(default=None, max_length=128)

    architecture_node: ArchitectureNodeRef | None = None

    strategy_branch_id: str | None = Field(default=None, max_length=64)

    pin_current_strategy: bool | None = None

    tradeoff_lever: str | None = Field(default=None, max_length=128)

    sandbox_posture: str | None = Field(default=None, max_length=128)

    compare_pin_ids: list[str] | None = None

    consulting_profile: dict[str, Any] | None = None

    consulting_continuity: str | None = Field(default=None, max_length=MAX_STRING)



    @field_validator("active_task", "consulting_continuity", mode="before")

    @classmethod

    def sanitize_strings(cls, value: Any) -> Any:

        if value is None:

            return None

        stats = SanitizationStats()

        return sanitize_nested(value, stats=stats)



    @field_validator("intent_alternatives", "compare_pin_ids", mode="before")

    @classmethod

    def sanitize_string_lists(cls, value: Any) -> Any:

        if not isinstance(value, list):

            return None

        stats = SanitizationStats()

        cleaned = [

            item

            for item in sanitize_nested(value, stats=stats)

            if isinstance(item, str) and item

        ]

        limit = MAX_COMPARE_PINS if value is not None else 32

        return cleaned[:limit]



    @field_validator("current_panel_data", "consulting_profile", mode="before")

    @classmethod

    def sanitize_nested_dict(cls, value: Any) -> Any:

        if value is None:

            return None

        if not isinstance(value, dict):

            return None

        stats = SanitizationStats()

        cleaned = sanitize_nested(value, stats=stats)

        if not isinstance(cleaned, dict):

            return None

        encoded = json.dumps(cleaned, default=str)

        if len(encoded) > MAX_PANEL_DATA_BYTES:

            cleaned = json.loads(encoded[:MAX_PANEL_DATA_BYTES])

        return cleaned



    @field_validator("constraint_state", mode="before")

    @classmethod

    def sanitize_constraint_state(cls, value: Any) -> Any:

        if value is None:

            return None

        if not isinstance(value, dict):

            return None

        stats = SanitizationStats()

        cleaned = sanitize_nested(value, stats=stats)

        if not isinstance(cleaned, dict):

            return None

        slots = cleaned.get("slots")

        if isinstance(slots, dict) and len(slots) > MAX_CONSTRAINT_SLOTS:

            cleaned["slots"] = dict(list(slots.items())[:MAX_CONSTRAINT_SLOTS])

        return cleaned





def validate_client_context(raw: dict[str, Any] | None) -> tuple[dict[str, Any], SanitizationStats]:

    """Parse and return safe client_context + sanitization stats."""

    stats = SanitizationStats()

    if not raw:

        return {}, stats

    if "constraints" in raw:
        stats.flat_constraints_rejected = 1
        logger.error(
            "rejected legacy flat constraints key; use constraint_state only"
        )
        raw = {k: v for k, v in raw.items() if k != "constraints"}

    try:

        encoded = json.dumps(raw, default=str)

        if len(encoded) > MAX_CLIENT_CONTEXT_JSON_BYTES:

            stats.truncated_strings += 1

            raw = json.loads(encoded[:MAX_CLIENT_CONTEXT_JSON_BYTES])

        allowed = set(ValidatedClientContext.model_fields.keys())

        filtered = {k: v for k, v in raw.items() if k in allowed}

        model = ValidatedClientContext.model_validate(filtered)

        result = model.model_dump(mode="json", exclude_none=True)

        if estimate_prompt_chars(result) > MAX_PROMPT_TOKEN_BUDGET_CHARS:

            logger.warning("client_context exceeds prompt budget; truncating active_task")

            if result.get("active_task"):

                result["active_task"] = str(result["active_task"])[:MAX_TASK]

        stats.total_chars = estimate_prompt_chars(result)

        return result, stats

    except Exception as exc:

        logger.warning("client_context validation failed: %s", exc)

        return {}, stats


