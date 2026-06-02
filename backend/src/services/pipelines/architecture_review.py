"""Architecture review — deterministic rule findings (Phase-2)."""

from __future__ import annotations

from typing import Any

from src.schemas.advisor_trace import AdvisorTrace
from src.schemas.constraint_state import ConstraintState
from src.services.pipelines.base import PipelineResult, RecommendationPipeline


class ArchitectureReviewPipeline(RecommendationPipeline):
    playbook_id = "architecture_review"

    async def run(
        self,
        state: ConstraintState,
        *,
        trace: AdvisorTrace | None = None,
        panel_data: dict | None = None,
        **kwargs: Any,
    ) -> PipelineResult:
        trace = trace or AdvisorTrace(
            playbook_id=self.playbook_id,
            constraint_snapshot=state.slot_values(),
        )
        nodes = (panel_data or {}).get("nodes") or []
        trace.retrieved = [
            str(n.get("slug") or n.get("id"))
            for n in nodes
            if isinstance(n, dict)
        ]
        findings = self._findings(panel_data or {})
        trace.log_step(f"filter/score: {len(findings)} architecture findings")
        trace.shortlist = [f["id"] for f in findings]
        return PipelineResult(
            shortlist=trace.shortlist,
            weights={},
            trace=trace,
            extra={"findings": findings},
        )

    def preview_signature(self, state: ConstraintState, **kwargs: Any) -> str:
        return "architecture_review"

    @staticmethod
    def _findings(panel_data: dict) -> list[dict[str, str]]:
        nodes = panel_data.get("nodes") if isinstance(panel_data, dict) else []
        text = " ".join(
            str(node.get(key, ""))
            for node in nodes
            if isinstance(node, dict)
            for key in ("id", "label", "category", "slug")
        ).lower()
        findings: list[dict[str, str]] = []
        if "rerank" not in text and "cohere" not in text:
            findings.append({
                "id": "missing_reranker",
                "severity": "high",
                "message": "Add a reranking stage after retrieval.",
            })
        if "eval" not in text and "langfuse" not in text and "ragas" not in text:
            findings.append({
                "id": "missing_eval",
                "severity": "medium",
                "message": "Add observability/evaluation (e.g. Langfuse or Ragas).",
            })
        if "chunk" not in text:
            findings.append({
                "id": "missing_chunk",
                "severity": "medium",
                "message": "Explicit chunking stage is not visible.",
            })
        return findings
