"""Local AI stack playbook — deterministic stack selection (Phase-2)."""

from __future__ import annotations

from typing import Any

from src.schemas.advisor_trace import AdvisorTrace
from src.schemas.constraint_state import ConstraintState
from src.services.pipelines.base import PipelineResult, RecommendationPipeline
from src.services.scoring import comparison_dimension_weights


class LocalAiStackPipeline(RecommendationPipeline):
    playbook_id = "local_ai_stack"

    async def run(
        self,
        state: ConstraintState,
        *,
        trace: AdvisorTrace | None = None,
        **kwargs: Any,
    ) -> PipelineResult:
        trace = trace or AdvisorTrace(
            playbook_id=self.playbook_id,
            constraint_snapshot=state.slot_values(),
        )
        agent_slug = "langchain" if state.get("agent_complexity") == "single_agent" else "crewai"
        model_label = "Llama 3.2 3B/8B" if state.get("hardware") == "cpu_only" else "Llama 3.2/3.3 8B"
        trace.log_step("score: deterministic local stack template")
        trace.shortlist = [agent_slug, "ollama"]
        nodes = [
            {"id": "app", "label": "Your App", "category": "agent_systems"},
            {
                "id": "agent",
                "label": "LangChain Agent" if agent_slug == "langchain" else "CrewAI",
                "slug": agent_slug,
                "category": "agent_systems",
            },
            {"id": "ollama", "label": "Ollama", "slug": "ollama", "category": "llm_layer"},
            {"id": "model", "label": model_label, "category": "llm_layer"},
        ]
        edges = [
            {"from": "app", "to": "agent"},
            {"from": "agent", "to": "ollama"},
            {"from": "ollama", "to": "model"},
        ]
        return PipelineResult(
            shortlist=trace.shortlist,
            weights=comparison_dimension_weights(state),
            trace=trace,
            extra={"nodes": nodes, "edges": edges},
        )

    def preview_signature(self, state: ConstraintState, **kwargs: Any) -> str:
        agent = "langchain" if state.get("agent_complexity") == "single_agent" else "crewai"
        hw = state.get("hardware") or "unknown"
        return f"{agent}|ollama|{hw}"
