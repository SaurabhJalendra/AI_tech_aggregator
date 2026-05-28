"""Strategic infrastructure consulting intelligence (Phase-5)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from src.schemas.advisor_trace import AdvisorTrace
from src.schemas.constraint_state import ConstraintSource, ConstraintState
from src.services.architecture_consulting import build_architecture_consulting

STRATEGY_BRANCHES: dict[str, dict[str, Any]] = {
    "cost_first": {
        "label": "Cost-first",
        "summary": "Minimize spend and operational overhead at the expense of premium managed features.",
        "slots": {"budget": "low", "operational_complexity_tolerance": "low"},
    },
    "scale_first": {
        "label": "Scalability-first",
        "summary": "Prioritize retrieval throughput, index growth, and production-grade resilience.",
        "slots": {"scale": "enterprise", "latency_priority": "critical"},
    },
    "low_ops": {
        "label": "Low-ops",
        "summary": "Favor managed services and reduced day-two operational burden.",
        "slots": {"deployment_preference": "managed", "operational_complexity_tolerance": "low"},
    },
    "privacy_first": {
        "label": "Privacy-first",
        "summary": "Emphasize data control, residency, and self-hosted deployment paths.",
        "slots": {
            "deployment_preference": "self_hosted",
            "data_sensitivity": "high",
            "prefer_open_source": True,
        },
    },
}

DUAL_STRATEGY_PATTERNS: list[tuple[str, str, str, dict[str, Any], dict[str, Any]]] = [
    (
        r"managed\s+vs\.?\s+self[- ]?host",
        "Managed cloud",
        "Self-hosted control",
        {"deployment_preference": "managed"},
        {"deployment_preference": "self_hosted"},
    ),
    (
        r"self[- ]?host(?:ed)?\s+vs\.?\s+managed",
        "Self-hosted control",
        "Managed cloud",
        {"deployment_preference": "self_hosted"},
        {"deployment_preference": "managed"},
    ),
    (
        r"low[- ]?cost\s+vs\.?\s+enterprise",
        "Cost-conscious",
        "Enterprise-grade",
        {"budget": "low", "scale": "prototype"},
        {"budget": "high", "scale": "enterprise"},
    ),
    (
        r"rapid\s+iteration\s+vs\.?\s+reliability",
        "Rapid iteration",
        "Reliability-first",
        {"scale": "prototype", "operational_complexity_tolerance": "low"},
        {"scale": "enterprise", "latency_priority": "critical"},
    ),
    (
        r"pinecone\s+vs\.?\s+qdrant",
        "Pinecone-oriented",
        "Qdrant-oriented",
        {"deployment_preference": "managed"},
        {"deployment_preference": "self_hosted", "prefer_open_source": True},
    ),
]


@dataclass
class DualStrategySpec:
    left_label: str
    right_label: str
    left_slots: dict[str, Any]
    right_slots: dict[str, Any]
    comparison_theme: str


def detect_dual_strategy_request(message: str) -> DualStrategySpec | None:
    lower = message.lower().strip()
    if not any(
        token in lower
        for token in (" vs ", " versus ", "compare ", "comparison between", "side by side")
    ):
        return None
    for pattern, left_l, right_l, left_slots, right_slots in DUAL_STRATEGY_PATTERNS:
        if re.search(pattern, lower):
            theme = f"{left_l} vs {right_l}"
            return DualStrategySpec(
                left_label=left_l,
                right_label=right_l,
                left_slots=left_slots,
                right_slots=right_slots,
                comparison_theme=theme,
            )
    if "managed" in lower and "self" in lower:
        return DualStrategySpec(
            left_label="Managed cloud",
            right_label="Self-hosted control",
            left_slots={"deployment_preference": "managed"},
            right_slots={"deployment_preference": "self_hosted"},
            comparison_theme="Managed vs self-hosted",
        )
    return None


def detect_strategy_branch_from_message(message: str) -> str | None:
    """Infer strategy branch when user types an explore message instead of clicking a chip."""
    lower = message.lower()
    if "explore" not in lower and "strategy" not in lower:
        return None
    branch_patterns: list[tuple[str, str]] = [
        (r"cost[- ]?first", "cost_first"),
        (r"scal(?:e|ability)[- ]?first", "scale_first"),
        (r"low[- ]?ops", "low_ops"),
        (r"privacy[- ]?first", "privacy_first"),
    ]
    for pattern, branch_id in branch_patterns:
        if re.search(pattern, lower):
            return branch_id
    return None


def apply_branch_slots(
    base: ConstraintState,
    branch_id: str,
) -> ConstraintState | None:
    branch = STRATEGY_BRANCHES.get(branch_id)
    if not branch:
        return None
    trial = base.model_copy(deep=True)
    for key, value in branch["slots"].items():
        trial.set_slot(
            key,
            value,
            source=ConstraintSource.EXPLICIT,
            confidence=1.0,
            force=True,
        )
    return trial


def build_strategy_branches(base: ConstraintState) -> list[dict[str, Any]]:
    """Explorable infrastructure strategy branches from current constraints."""
    branches: list[dict[str, Any]] = []
    for branch_id, meta in STRATEGY_BRANCHES.items():
        trial = apply_branch_slots(base, branch_id)
        if trial is None:
            continue
        branches.append(
            {
                "id": branch_id,
                "label": meta["label"],
                "summary": meta["summary"],
                "slot_preview": meta["slots"],
                "operational_consequence": _branch_operational_consequence(branch_id),
                "future_tradeoff": _branch_future_tradeoff(branch_id),
            }
        )
    return branches


def _branch_operational_consequence(branch_id: str) -> str:
    mapping = {
        "cost_first": "Lower spend often means more hands-on tuning and fewer premium managed features.",
        "scale_first": "Higher scale readiness increases indexing, observability, and platform coordination needs.",
        "low_ops": "Managed paths reduce toil but may introduce vendor coupling over time.",
        "privacy_first": "Self-hosted control adds deployment and security ownership responsibilities.",
    }
    return mapping.get(branch_id, "Tradeoffs shift across operational burden and flexibility.")


def _branch_future_tradeoff(branch_id: str) -> str:
    mapping = {
        "cost_first": "Future growth may require revisiting managed retrieval or replication sooner than planned.",
        "scale_first": "You gain headroom for traffic spikes but accept higher baseline operational maturity.",
        "low_ops": "Day-two burden stays lower; migration planning matters if vendor terms change.",
        "privacy_first": "Compliance wins early; automation investment typically follows as teams scale.",
    }
    return mapping.get(branch_id, "Revisit constraints as workload and governance requirements evolve.")


def compare_strategy_postures(
    left_consulting: dict[str, Any],
    right_consulting: dict[str, Any],
    *,
    left_label: str,
    right_label: str,
    theme: str,
) -> dict[str, Any]:
    """Consulting-grade dual-architecture comparison (not a feature matrix)."""
    left_posture = left_consulting.get("operational_posture") or {}
    right_posture = right_consulting.get("operational_posture") or {}

    dimensions = [
        {
            "dimension": "Operational posture",
            "left": left_consulting.get("comparative_priority_line") or left_label,
            "right": right_consulting.get("comparative_priority_line") or right_label,
            "insight": _posture_insight(left_posture, right_posture),
        },
        {
            "dimension": "Scaling implications",
            "left": left_consulting.get("scaling_rationale") or "—",
            "right": right_consulting.get("scaling_rationale") or "—",
            "insight": "Compare when retrieval volume and concurrent queries outpace current indexing.",
        },
        {
            "dimension": "Deployment burden",
            "left": left_posture.get("deployment_burden", "—"),
            "right": right_posture.get("deployment_burden", "—"),
            "insight": "Self-managed paths trade convenience for control; managed paths invert that tradeoff.",
        },
        {
            "dimension": "Long-term complexity",
            "left": left_consulting.get("operational_complexity", "—"),
            "right": right_consulting.get("operational_complexity", "—"),
            "insight": "Operational complexity compounds with team size, compliance scope, and traffic growth.",
        },
        {
            "dimension": "Ecosystem tradeoffs",
            "left": _ecosystem_line(left_consulting),
            "right": _ecosystem_line(right_consulting),
            "insight": "Open-source flexibility vs managed convenience shapes hiring, tooling, and migration paths.",
        },
    ]

    return {
        "theme": theme,
        "left_label": left_label,
        "right_label": right_label,
        "dimensions": dimensions,
        "consulting_summary": (
            f"Strategic comparison: **{theme}**. "
            "Review operational posture and scaling paths — not feature checklists."
        ),
    }


def _posture_insight(left: dict[str, Any], right: dict[str, Any]) -> str:
    if left.get("deployment_burden") != right.get("deployment_burden"):
        return "Deployment model is the primary driver of day-two operational shape."
    if left.get("scaling_pressure") != right.get("scaling_pressure"):
        return "Scaling pressure differs — plan capacity before latency becomes user-visible."
    return "Both strategies are viable; the choice depends on tolerance for operational ownership."


def _ecosystem_line(consulting: dict[str, Any]) -> str:
    snapshot = consulting.get("constraint_snapshot") or {}
    if snapshot.get("prefer_open_source"):
        return "Open-source ecosystem flexibility"
    deploy = snapshot.get("deployment_preference") or snapshot.get("deployment")
    if deploy in ("managed", "cloud"):
        return "Managed vendor ecosystem"
    return "Balanced integration ecosystem"


def build_strategic_forecasts(
    state: ConstraintState,
    trace: AdvisorTrace,
    selections: dict[str, str],
    *,
    operational_stress: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Future-oriented consulting forecasts — calm and professional."""
    forecasts: list[dict[str, str]] = []
    scale = state.get("scale")
    deploy = state.get("deployment_preference") or state.get("deployment")

    if scale in ("growing_application", "enterprise"):
        forecasts.append(
            {
                "horizon": "medium_term",
                "title": "Scaling bottleneck",
                "insight": (
                    "At enterprise scale, this deployment model may require operational automation "
                    "for indexing, replication, and incident response."
                ),
            }
        )
    if "retrieval" in selections or "vector_databases" in selections:
        if state.get("latency_priority") == "critical" or scale != "prototype":
            forecasts.append(
                {
                    "horizon": "near_term",
                    "title": "Retrieval latency",
                    "insight": (
                        "Reranking and retrieval latency may become a bottleneck under higher "
                        "concurrency — plan caching and index tuning early."
                    ),
                }
            )
    if deploy in ("managed", "cloud"):
        forecasts.append(
            {
                "horizon": "long_term",
                "title": "Ecosystem lock-in",
                "insight": (
                    "Managed retrieval APIs reduce toil but can create vendor coupling — "
                    "document export paths and index portability before production hardening."
                ),
            }
        )
    elif deploy in ("self_hosted", "on_prem"):
        forecasts.append(
            {
                "horizon": "medium_term",
                "title": "Operational burden",
                "insight": (
                    "Self-hosted components often shift cost from licenses to platform engineering — "
                    "budget for observability and upgrade cadence as traffic grows."
                ),
            }
        )
    if operational_stress and operational_stress.get("retrieval_bottleneck_risk") == "elevated":
        forecasts.append(
            {
                "horizon": "near_term",
                "title": "Load stress",
                "insight": (
                    "Under simulated load pressure, retrieval and reranking stages warrant "
                    "capacity review before user-facing SLAs tighten."
                ),
            }
        )
    if len(trace.filtered_out) > 6:
        forecasts.append(
            {
                "horizon": "strategic",
                "title": "Constraint flexibility",
                "insight": (
                    "Many alternatives were filtered by current constraints — revisiting budget "
                    "or deployment posture can reopen viable paths without replatforming everything."
                ),
            }
        )
    if not forecasts:
        forecasts.append(
            {
                "horizon": "medium_term",
                "title": "Cost evolution",
                "insight": (
                    "Embedding and retrieval costs typically dominate RAG spend as usage grows — "
                    "instrument usage before scale surprises the budget."
                ),
            }
        )
    return forecasts[:5]


def build_operational_stress(
    state: ConstraintState,
    *,
    simulation_active: bool = False,
) -> dict[str, Any]:
    """Subtle operational realism — consulting grade, not DevOps telemetry."""
    scale = state.get("scale")
    deploy = state.get("deployment_preference") or state.get("deployment")
    latency = state.get("latency_priority")

    scaling_pressure = "moderate"
    if scale in ("enterprise", "growing_application") or simulation_active:
        scaling_pressure = "elevated"

    retrieval_risk = "moderate"
    if latency == "critical" or scale in ("enterprise", "growing_application"):
        retrieval_risk = "elevated"

    fragility = "low"
    if deploy in ("self_hosted", "on_prem") and scale != "prototype":
        fragility = "medium"

    return {
        "scaling_pressure": scaling_pressure,
        "retrieval_bottleneck_risk": retrieval_risk,
        "operational_fragility": fragility,
        "deployment_pressure": (
            "elevated" if deploy in ("self_hosted", "on_prem") and scale != "prototype" else "moderate"
        ),
        "latency_stress": "elevated" if latency == "critical" else "moderate",
        "consulting_note": (
            "Stress indicators reflect strategic posture — not live metrics."
        ),
    }


def enrich_architecture_consulting(
    consulting: dict[str, Any],
    *,
    state: ConstraintState,
    trace: AdvisorTrace,
    selections: dict[str, str],
    simulation_active: bool = False,
    consulting_profile: dict[str, Any] | None = None,
    evolution_history: list[dict[str, Any]] | None = None,
    strategy_comparison: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach strategic consulting intelligence to architecture_consulting."""
    stress = build_operational_stress(state, simulation_active=simulation_active)
    consulting["operational_stress"] = stress
    consulting["strategic_forecasts"] = build_strategic_forecasts(
        state, trace, selections, operational_stress=stress
    )
    consulting["strategy_branches"] = build_strategy_branches(state)
    if consulting_profile:
        continuity = consulting.get("continuity_framing")
        profile_line = None
        from src.services.consulting_memory import build_continuity_framing

        profile_line = build_continuity_framing(consulting_profile)
        if profile_line:
            consulting["consulting_continuity"] = profile_line
        elif continuity:
            consulting["consulting_continuity"] = continuity
    if evolution_history:
        consulting["evolution_history"] = evolution_history[:8]
    if strategy_comparison:
        consulting["strategy_comparison"] = strategy_comparison

    pinned = None
    if consulting_profile:
        workspace = consulting_profile.get("strategy_workspace") or {}
        pinned = workspace.get("pinned") or []

    from src.services.phase6_intelligence import enrich_phase6

    enrich_phase6(
        consulting,
        state=state,
        trace=trace,
        selections=selections,
        stress=stress,
        consulting_profile=consulting_profile,
        evolution_history=evolution_history,
        pinned_strategies=pinned,
    )
    return consulting


async def build_multi_pin_strategy_overview(
    db,
    pipeline,
    pins: list[dict[str, Any]],
    base_state: ConstraintState,
    *,
    playbook_id: str = "rag_pipeline_design",
) -> dict[str, Any] | None:
    """Compare multiple pinned architecture futures (consulting summaries)."""
    from src.services.phase6_intelligence import (
        build_cost_evolution_intelligence,
        build_organizational_intelligence,
    )

    strategies: list[dict[str, Any]] = []
    for pin in pins[:3]:
        snap = pin.get("constraint_snapshot")
        if isinstance(snap, dict) and snap.get("slots"):
            pin_state = ConstraintState.model_validate(snap)
        else:
            pin_state = base_state.model_copy(deep=True)

        result = await pipeline.run(pin_state)
        extra = result.extra or {}
        sel = extra.get("selections") or pin.get("selections") or {}
        consulting = build_architecture_consulting(
            trace=result.trace,
            state=pin_state,
            playbook_id=playbook_id,
            selections=sel,
            stage_decisions=extra.get("stage_decisions"),
        )
        strategies.append(
            {
                "pin_id": pin.get("id"),
                "title": pin.get("title"),
                "selections": sel,
                "comparative_priority_line": consulting.get("comparative_priority_line"),
                "operational_posture": consulting.get("operational_posture"),
                "scaling_rationale": consulting.get("scaling_rationale"),
                "cost_evolution": build_cost_evolution_intelligence(pin_state),
                "organizational": build_organizational_intelligence(pin_state),
            }
        )

    if len(strategies) < 2:
        return None

    return {
        "theme": "Pinned architecture futures",
        "strategies": strategies,
        "consulting_summary": (
            "Comparing saved strategy alternatives — focus on operational posture, "
            "cost evolution, and organizational fit rather than feature lists."
        ),
    }


async def build_dual_strategy_comparison(
    db,
    pipeline,
    base_state: ConstraintState,
    spec: DualStrategySpec,
    *,
    playbook_id: str = "rag_pipeline_design",
) -> dict[str, Any] | None:
    """Run pipeline twice and produce side-by-side strategy comparison payload."""
    left_state = base_state.model_copy(deep=True)
    right_state = base_state.model_copy(deep=True)
    for key, val in spec.left_slots.items():
        left_state.set_slot(key, val, source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)
    for key, val in spec.right_slots.items():
        right_state.set_slot(key, val, source=ConstraintSource.EXPLICIT, confidence=1.0, force=True)

    left_result = await pipeline.run(left_state)
    right_result = await pipeline.run(right_state)
    if not (left_result.extra and left_result.extra.get("nodes")):
        return None
    if not (right_result.extra and right_result.extra.get("nodes")):
        return None

    left_sel = left_result.extra.get("selections") or {}
    right_sel = right_result.extra.get("selections") or {}

    left_consulting = build_architecture_consulting(
        trace=left_result.trace,
        state=left_state,
        playbook_id=playbook_id,
        selections=left_sel,
        stage_decisions=left_result.extra.get("stage_decisions"),
    )
    right_consulting = build_architecture_consulting(
        trace=right_result.trace,
        state=right_state,
        playbook_id=playbook_id,
        selections=right_sel,
        stage_decisions=right_result.extra.get("stage_decisions"),
    )

    comparison = compare_strategy_postures(
        left_consulting,
        right_consulting,
        left_label=spec.left_label,
        right_label=spec.right_label,
        theme=spec.comparison_theme,
    )
    comparison["left_architecture"] = {
        "title": spec.left_label,
        "nodes": left_result.extra.get("nodes") or [],
        "edges": left_result.extra.get("edges") or [],
        "selections": left_sel,
        "architecture_consulting": left_consulting,
    }
    comparison["right_architecture"] = {
        "title": spec.right_label,
        "nodes": right_result.extra.get("nodes") or [],
        "edges": right_result.extra.get("edges") or [],
        "selections": right_sel,
        "architecture_consulting": right_consulting,
    }
    comparison["left_trace"] = left_result.trace
    comparison["right_trace"] = right_result.trace
    return comparison
