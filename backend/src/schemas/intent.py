"""Structured outputs for semantic intent routing (advisor domain)."""

from pydantic import BaseModel, Field


class IntentMatchEvidence(BaseModel):
    """One piece of evidence supporting an intent decision."""

    exemplar_id: str
    exemplar_text: str
    intent_id: str
    similarity: float = Field(ge=-1.0, le=1.0, description="Cosine similarity to query embedding")


class IntentAlternative(BaseModel):
    """Second-best intent candidate for debugging and clarification copy."""

    intent_id: str
    score: float


class IntentResult(BaseModel):
    """Output of the semantic intent layer for planner + LLM consumption."""

    intent_id: str = Field(
        description="Registry intent id, e.g. category:vector_databases or rag_pipeline"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Best aggregated similarity score for the winning intent",
    )
    margin: float | None = Field(
        default=None,
        description="Gap between best and second-best intent scores (None if unavailable)",
    )
    matched_evidence: list[IntentMatchEvidence] = Field(
        default_factory=list,
        description="Top exemplar matches (typically 1–3) backing the decision",
    )
    inferred_parameters: dict = Field(
        default_factory=dict,
        description="Planner-ready hints, e.g. category slug for category:* intents",
    )
    needs_clarification: bool = Field(
        default=False,
        description="True when confidence is in an ambiguous band or top intents tie",
    )
    clarification_prompt: str | None = Field(
        default=None,
        description="Short user-facing question when needs_clarification is True",
    )
    alternatives: list[IntentAlternative] = Field(
        default_factory=list,
        description="Next-best intent scores for telemetry and prompts",
    )
