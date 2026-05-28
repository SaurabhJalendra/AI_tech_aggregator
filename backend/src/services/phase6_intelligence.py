"""Phase-6 strategic infrastructure intelligence (organizational, lifecycle, foresight)."""

from __future__ import annotations

from typing import Any

from src.schemas.advisor_trace import AdvisorTrace
from src.schemas.constraint_state import ConstraintState

TRADEOFF_LEVERS: dict[str, dict[str, Any]] = {
    "lower_latency": {
        "label": "Lower latency",
        "slots": {"latency_priority": "critical"},
        "tradeoff": "May increase cost and operational tuning effort.",
    },
    "lower_ops": {
        "label": "Lower operational burden",
        "slots": {"deployment_preference": "managed", "operational_complexity_tolerance": "low"},
        "tradeoff": "Less infrastructure control; vendor coupling may grow over time.",
    },
    "lower_cost": {
        "label": "Lower cost",
        "slots": {"budget": "low"},
        "tradeoff": "Fewer premium managed features; more hands-on optimization.",
    },
    "higher_scale": {
        "label": "Higher scalability",
        "slots": {"scale": "enterprise", "latency_priority": "critical"},
        "tradeoff": "Higher operational maturity and observability investment.",
    },
    "privacy": {
        "label": "Stronger privacy",
        "slots": {"data_sensitivity": "high", "deployment_preference": "self_hosted"},
        "tradeoff": "Platform engineering ownership increases.",
    },
    "simpler_deploy": {
        "label": "Simpler deployment",
        "slots": {"deployment_preference": "managed", "operational_complexity_tolerance": "low"},
        "tradeoff": "Customization and residency options may narrow.",
    },
    "better_observability": {
        "label": "Observability focus",
        "slots": {"operational_complexity_tolerance": "medium", "scale": "growing_application"},
        "tradeoff": "Instrumentation overhead grows with pipeline stages.",
    },
}

SANDBOX_POSTURES: list[dict[str, Any]] = [
    {
        "id": "prototype",
        "label": "Prototype pace",
        "slots": {"scale": "prototype", "budget": "low"},
    },
    {
        "id": "production",
        "label": "Production growth",
        "slots": {"scale": "growing_application", "budget": "medium"},
    },
    {
        "id": "enterprise",
        "label": "Enterprise scale",
        "slots": {"scale": "enterprise", "latency_priority": "critical"},
    },
    {
        "id": "managed",
        "label": "Managed-first",
        "slots": {"deployment_preference": "managed"},
    },
    {
        "id": "self_hosted",
        "label": "Self-hosted control",
        "slots": {"deployment_preference": "self_hosted"},
    },
]


def apply_tradeoff_lever(state: ConstraintState, lever_id: str) -> ConstraintState | None:
    from src.schemas.constraint_state import ConstraintSource

    lever = TRADEOFF_LEVERS.get(lever_id)
    if not lever:
        return None
    trial = state.model_copy(deep=True)
    for key, value in lever["slots"].items():
        trial.set_slot(
            key,
            value,
            source=ConstraintSource.EXPLICIT,
            confidence=1.0,
            force=True,
        )
    return trial


def build_tradeoff_simulator(state: ConstraintState) -> list[dict[str, Any]]:
    """Interactive strategic tradeoff levers for the blueprint sandbox."""
    items: list[dict[str, Any]] = []
    for lever_id, meta in TRADEOFF_LEVERS.items():
        items.append(
            {
                "id": lever_id,
                "label": meta["label"],
                "tradeoff": meta["tradeoff"],
                "active": _lever_matches_state(state, meta["slots"]),
            }
        )
    return items


def _lever_matches_state(state: ConstraintState, slots: dict[str, Any]) -> bool:
    return all(state.get(k) == v for k, v in slots.items())


def build_architecture_sandbox(state: ConstraintState) -> dict[str, Any]:
    return {
        "postures": SANDBOX_POSTURES,
        "active_posture": _detect_active_posture(state),
        "constraint_summary": {
            "scale": state.get("scale"),
            "budget": state.get("budget") or state.get("budget_tier"),
            "deployment": state.get("deployment_preference") or state.get("deployment"),
        },
    }


def _detect_active_posture(state: ConstraintState) -> str | None:
    for posture in SANDBOX_POSTURES:
        if all(state.get(k) == v for k, v in posture["slots"].items()):
            return posture["id"]
    return None


def build_organizational_intelligence(
    state: ConstraintState,
    consulting_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Consultative organizational fit — not judgmental."""
    scale = state.get("scale")
    deploy = state.get("deployment_preference") or state.get("deployment")
    ops_tolerance = state.get("operational_complexity_tolerance") or "medium"
    team_maturity = state.get("team_maturity") or state.get("platform_maturity")

    insights: list[str] = []
    if deploy in ("self_hosted", "on_prem") and scale in ("enterprise", "growing_application"):
        insights.append(
            "This architecture may introduce meaningful operational ownership — "
            "platform engineering capacity becomes a strategic dependency."
        )
    if deploy in ("managed", "cloud") and scale == "prototype":
        insights.append(
            "Managed deployment may reduce operational overhead for rapidly iterating teams "
            "while you validate product-market fit."
        )
    if ops_tolerance == "low" and deploy in ("self_hosted", "on_prem"):
        insights.append(
            "Self-hosted components alongside low operational tolerance can create tension — "
            "consider phased managed adoption for non-critical stages."
        )
    if team_maturity in ("small", "early", "limited") or (
        consulting_profile
        and consulting_profile.get("organizational_context", {}).get("team_size") == "small"
    ):
        insights.append(
            "Smaller platform teams often benefit from narrowing the number of self-managed "
            "stages until operational playbooks mature."
        )
    if not insights:
        insights.append(
            "Align staffing and on-call expectations with deployment choices before scale "
            "amplifies operational load."
        )

    return {
        "team_maturity_signal": team_maturity or "unspecified",
        "operational_capability": (
            "stronger managed-leaning" if deploy in ("managed", "cloud") else "self-managed leaning"
        ),
        "ownership_burden": (
            "higher" if deploy in ("self_hosted", "on_prem") else "moderate"
        ),
        "insights": insights[:3],
    }


def build_lifecycle_intelligence(
    state: ConstraintState,
    selections: dict[str, str],
) -> dict[str, Any]:
    """Infrastructure evolution and aging — long-term consulting."""
    scale = state.get("scale")
    deploy = state.get("deployment_preference") or state.get("deployment")
    notes: list[str] = []

    if scale in ("enterprise", "growing_application") and deploy in ("managed", "cloud"):
        notes.append(
            "At enterprise scale, managed vector infrastructure may become operationally "
            "inefficient if index portability and cost governance lag behind growth."
        )
    if scale != "prototype" and "evaluation" not in selections:
        notes.append(
            "As architecture ages, quality evaluation stages often become migration pressure "
            "points — plan instrumentation before regressions reach users."
        )
    if len(selections) >= 5:
        notes.append(
            "Multi-stage pipelines accumulate technical debt when orchestration and "
            "observability do not evolve with traffic — schedule periodic architecture reviews."
        )
    if deploy in ("self_hosted", "on_prem"):
        notes.append(
            "Self-hosted stacks may require future migration windows for major version upgrades "
            "and security patching — document rollback paths early."
        )
    if not notes:
        notes.append(
            "Monitor ecosystem maturity of chosen components; consolidation in the market "
            "can shift migration pressure over a 12–24 month horizon."
        )

    return {
        "migration_pressure": "elevated" if scale == "enterprise" else "moderate",
        "maintainability_trend": (
            "increasing complexity" if len(selections) >= 6 else "manageable with discipline"
        ),
        "replacement_timing": (
            "plan before enterprise traffic" if scale != "prototype" else "revisit at growth inflection"
        ),
        "notes": notes[:4],
    }


def build_cost_evolution_intelligence(state: ConstraintState) -> dict[str, Any]:
    """Future cost trajectories — consulting-oriented, not financial dashboards."""
    scale = state.get("scale")
    deploy = state.get("deployment_preference") or state.get("deployment")
    budget = state.get("budget") or state.get("budget_tier")

    trajectories: list[dict[str, str]] = []

    if scale in ("growing_application", "enterprise"):
        trajectories.append(
            {
                "title": "Retrieval volume",
                "insight": (
                    "At higher retrieval volume, managed vector infrastructure may become "
                    "significantly more expensive than self-hosted alternatives — model unit "
                    "economics before committing."
                ),
            }
        )
    if deploy in ("self_hosted", "on_prem"):
        trajectories.append(
            {
                "title": "Hidden operational cost",
                "insight": (
                    "Operational staffing and platform engineering time often dominate "
                    "self-hosted TCO — budget indirectly through headcount and on-call load."
                ),
            }
        )
    elif deploy in ("managed", "cloud"):
        trajectories.append(
            {
                "title": "Managed cost curve",
                "insight": (
                    "Managed APIs scale cost linearly with usage — advantageous early, "
                    "worth revisiting at sustained enterprise query rates."
                ),
            }
        )
    if budget == "low":
        trajectories.append(
            {
                "title": "Cost discipline",
                "insight": (
                    "Low-budget posture favors fewer premium stages; migration costs spike "
                    "if you later add enterprise features without architectural slack."
                ),
            }
        )
    if not trajectories:
        trajectories.append(
            {
                "title": "Baseline spend",
                "insight": (
                    "Embedding and generation costs typically outpace storage — instrument "
                    "both as usage grows."
                ),
            }
        )

    return {"trajectories": trajectories[:4], "cost_posture": budget or "balanced"}


def build_ecosystem_evolution(
    selections: dict[str, str],
    state: ConstraintState,
) -> dict[str, Any]:
    """Ecosystem trajectory — calm and strategic."""
    open_source_bias = state.get("prefer_open_source")
    insights: list[str] = []

    if open_source_bias:
        insights.append(
            "Open-source ecosystems evolve rapidly — commit to upgrade cadence and "
            "community health checks for core stages."
        )
    slugs = list(selections.values())
    if len(set(slugs)) >= 4:
        insights.append(
            "A multi-vendor toolchain may face ecosystem fragmentation — consolidation "
            "or managed bridges can reduce long-term integration tax."
        )
    if "vector_databases" in selections:
        insights.append(
            "The vector database landscape is consolidating — document export and "
            "index migration paths to mitigate vendor trajectory risk."
        )
    if not insights:
        insights.append(
            "Track ecosystem maturity of your LLM and retrieval providers; API stability "
            "often matters more than feature velocity at production scale."
        )

    return {
        "stability": "evolving" if open_source_bias else "mixed",
        "lock_in_risk": "moderate" if state.get("deployment_preference") == "managed" else "lower",
        "insights": insights[:3],
    }


def build_confidence_calibration(
    trace: AdvisorTrace,
    state: ConstraintState,
) -> dict[str, Any]:
    """Realistic uncertainty — believable consulting."""
    n_filtered = len(trace.filtered_out)
    n_scores = len(trace.scores)
    scale = state.get("scale")

    if n_filtered > 8 or (scale == "prototype" and n_scores > 4):
        tone = "moderate"
        headline = "Moderate confidence"
        explanation = (
            "Workload patterns and constraints are still evolving — treat finalists as "
            "directional until operational data validates assumptions."
        )
    elif n_scores >= 4 and n_filtered >= 3:
        tone = "solid"
        headline = "Solid confidence"
        explanation = (
            "Deterministic scoring and constraint filtering align, though ecosystem "
            "shifts may reopen tradeoffs as you scale."
        )
    else:
        tone = "high"
        headline = "Strong alignment"
        explanation = (
            "Constraints and scoring evidence converge — remaining uncertainty is mainly "
            "organizational readiness and future traffic shape."
        )

    uncertainty_zones: list[str] = []
    if scale == "prototype":
        uncertainty_zones.append("Traffic shape and SLA targets may shift significantly after launch.")
    if state.get("deployment_preference") not in (None, "managed", "self_hosted"):
        uncertainty_zones.append("Deployment posture may need refinement as compliance scope clarifies.")

    return {
        "tone": tone,
        "headline": headline,
        "explanation": explanation,
        "uncertainty_zones": uncertainty_zones[:2],
    }


def build_infrastructure_pressure(
    stress: dict[str, Any],
    state: ConstraintState,
) -> dict[str, Any]:
    """Advanced operational realism — consulting grade."""
    scale = state.get("scale")
    base = dict(stress or {})
    saturation = "low"
    if (
        base.get("scaling_pressure") == "elevated"
        and base.get("retrieval_bottleneck_risk") == "elevated"
    ):
        saturation = "elevated"
    elif base.get("operational_fragility") == "medium":
        saturation = "moderate"

    base["operational_saturation"] = saturation
    base["maintenance_burden"] = (
        "elevated"
        if (state.get("deployment_preference") in ("self_hosted", "on_prem") and scale != "prototype")
        else "moderate"
    )
    base["observability_complexity"] = (
        "growing" if scale in ("enterprise", "growing_application") else "manageable"
    )
    return base


def build_strategic_timeline(
    evolution_history: list[dict[str, Any]] | None,
    decision_timeline: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Unified infrastructure strategy history."""
    entries: list[dict[str, Any]] = []
    for item in evolution_history or []:
        entries.append(
            {
                "type": "evolution",
                "title": item.get("title") or "Architecture state",
                "detail": item.get("summary") or item.get("transition_reason") or "",
                "at": item.get("created_at"),
            }
        )
    for item in decision_timeline or []:
        entries.append(
            {
                "type": item.get("type") or "decision",
                "title": item.get("title") or "Decision",
                "detail": item.get("detail") or "",
                "at": None,
            }
        )
    return entries[:12]


def build_simulation_reasoning(
    spec_label: str,
    state: ConstraintState,
    replacements: list[dict[str, Any]],
    selections: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Deeper simulation narrative beyond constraint mutation."""
    org = build_organizational_intelligence(state)
    lifecycle = build_lifecycle_intelligence(state, selections or {})
    return {
        "scenario": spec_label,
        "organizational_note": org["insights"][0] if org.get("insights") else None,
        "lifecycle_note": lifecycle["notes"][0] if lifecycle.get("notes") else None,
        "components_affected": len(replacements),
        "deterministic": True,
    }


def enrich_phase6(
    consulting: dict[str, Any],
    *,
    state: ConstraintState,
    trace: AdvisorTrace,
    selections: dict[str, str],
    stress: dict[str, Any],
    consulting_profile: dict[str, Any] | None = None,
    evolution_history: list[dict[str, Any]] | None = None,
    pinned_strategies: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Attach all Phase-6 intelligence blocks."""
    consulting["organizational_intelligence"] = build_organizational_intelligence(
        state, consulting_profile
    )
    consulting["lifecycle_intelligence"] = build_lifecycle_intelligence(state, selections)
    consulting["cost_evolution"] = build_cost_evolution_intelligence(state)
    consulting["ecosystem_evolution"] = build_ecosystem_evolution(selections, state)
    consulting["confidence_calibration"] = build_confidence_calibration(trace, state)
    consulting["operational_stress"] = build_infrastructure_pressure(stress, state)
    consulting["tradeoff_simulator"] = build_tradeoff_simulator(state)
    consulting["architecture_sandbox"] = build_architecture_sandbox(state)
    consulting["strategic_timeline"] = build_strategic_timeline(
        evolution_history,
        consulting.get("decision_timeline"),
    )
    if pinned_strategies:
        consulting["strategy_workspace"] = {
            "pinned": pinned_strategies[:5],
            "count": len(pinned_strategies),
        }
    return consulting
