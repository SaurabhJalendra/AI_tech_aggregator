"""Deterministic architecture consulting payload for Phase-3C blueprint intelligence."""

from __future__ import annotations

from typing import Any

from src.schemas.advisor_trace import AdvisorTrace, FilterRecord, ScoreRecord, user_visible_filters
from src.schemas.constraint_state import ConstraintState

_CATEGORY_LABELS: dict[str, str] = {
    "data_ingestion": "document intake",
    "chunking": "content preprocessing",
    "embeddings": "semantic embedding",
    "vector_databases": "semantic retrieval storage",
    "retrieval": "hybrid retrieval",
    "rag_architectures": "RAG orchestration",
    "llm_layer": "language generation",
    "agent_systems": "agent orchestration",
    "evaluation": "quality evaluation",
}

_SCALE_BADGES: dict[str, str] = {
    "enterprise": "Enterprise-scale",
    "growing_application": "Growing production",
    "prototype": "Prototype-friendly",
    "small": "Lightweight workload",
}

_COMPLEXITY_LABELS: dict[str, str] = {
    "low": "Lower operational complexity",
    "medium": "Moderate operational complexity",
    "high": "Higher operational complexity",
}


def _humanize_filter_reason(reason: str) -> str:
    mapping = {
        "budget=low excludes high tier": "exceeded your cost-efficiency preference",
        "python_sdk preference deprioritizes cloud-only API": "did not align with your Python/SDK integration preference",
    }
    return mapping.get(reason, reason.replace("_", " ").rstrip("."))


def _format_module_name(slug: str, label: str | None = None) -> str:
    if label:
        return label
    return slug.replace("_", " ").title()


def _comparative_priority_line(state: ConstraintState) -> str:
    deploy = state.get("deployment_preference") or state.get("deployment")
    budget = state.get("budget") or state.get("budget_tier")
    scale = state.get("scale")

    if deploy in ("self_hosted", "on_prem"):
        if budget == "low":
            return "Prioritizes deployment control and cost discipline over fully managed convenience."
        return "Prioritizes deployment control and data residency over maximum managed convenience."
    if deploy in ("managed", "cloud"):
        return "Prioritizes operational simplicity over maximum infrastructure customization."
    if budget == "low":
        return "Prioritizes cost efficiency over premium managed features."
    if scale in ("enterprise", "growing_application"):
        return "Prioritizes scalable retrieval patterns over rapid throwaway prototyping."
    if state.get("prefer_open_source"):
        return "Prioritizes open-source flexibility over proprietary convenience."
    return "Balances scalability, operational burden, and integration fit for your stated workload."


def _workload_framing(state: ConstraintState) -> str | None:
    scale = state.get("scale")
    use_case = state.get("use_case")
    parts: list[str] = []
    if scale in _SCALE_BADGES:
        parts.append(_SCALE_BADGES[scale].lower())
    elif scale:
        parts.append(str(scale).replace("_", " "))
    if use_case:
        parts.append(f"{str(use_case).replace('_', ' ')} workload")
    return " · ".join(parts) if parts else None


def _confidence_block(trace: AdvisorTrace, selections: dict[str, str]) -> dict[str, Any]:
    visible_filters = user_visible_filters(trace.filtered_out)
    n_stages = len(selections)
    n_scores = len(trace.scores)

    if n_stages >= 4 and n_scores >= n_stages and len(visible_filters) > 0:
        return {
            "tone": "high",
            "headline": "High-confidence architecture",
            "explanation": (
                "Each pipeline stage was filtered and scored against your constraints before "
                "placement in this blueprint."
            ),
            "evidence": [
                f"{n_stages} stages resolved with deterministic scoring",
                f"{len(visible_filters)} alternatives ruled out by your constraints",
            ],
        }
    if n_stages >= 2:
        return {
            "tone": "solid",
            "headline": "Advisor-engineered blueprint",
            "explanation": (
                "Components were selected to work together for your workload profile and "
                "constraint memory."
            ),
            "evidence": [
                f"{n_stages} core stages configured",
                "Selections backed by registry scoring",
            ],
        }
    return {
        "tone": "moderate",
        "headline": "Recommended starting architecture",
        "explanation": (
            "Explore each layer — constraints and alternatives refine as you iterate with the advisor."
        ),
        "evidence": ["Initial deterministic placement"],
    }


def _build_node_decision(
    *,
    category: str,
    selected_slug: str,
    selected_label: str,
    runners_up: list[dict[str, Any]],
    rejected: list[FilterRecord],
    state: ConstraintState,
    winner_score: float | None,
) -> dict[str, Any]:
    cat_label = _CATEGORY_LABELS.get(category, category.replace("_", " "))
    selected_name = _format_module_name(selected_slug, selected_label)

    reason_parts: list[str] = []
    deploy = state.get("deployment_preference") or state.get("deployment")
    if deploy in ("self_hosted", "on_prem"):
        reason_parts.append("self-hosting and deployment control mattered")
    elif deploy in ("managed", "cloud"):
        reason_parts.append("managed operational simplicity mattered")
    budget = state.get("budget") or state.get("budget_tier")
    if budget == "low":
        reason_parts.append("cost efficiency was prioritized")
    if state.get("language") == "python" or state.get("implementation_preference") == "python":
        reason_parts.append("Python ecosystem compatibility was prioritized")
    if winner_score is not None and winner_score >= 7.5:
        reason_parts.append("scored strongest for this pipeline stage")

    selection_reason = (
        f"{selected_name} was selected for {cat_label}"
        + (f" because {', '.join(reason_parts)}." if reason_parts else ".")
    )

    considered = [
        {
            "slug": r["slug"],
            "label": _format_module_name(r["slug"], r.get("label")),
            "score": r.get("score"),
            "outcome": "runner_up",
        }
        for r in runners_up
        if r.get("slug") != selected_slug
    ][:3]

    rejected_out = [
        {
            "slug": rec.slug,
            "label": _format_module_name(rec.slug),
            "reason": _humanize_filter_reason(rec.reason),
        }
        for rec in rejected
        if rec.slug != selected_slug
    ][:4]

    tradeoffs: list[str] = []
    if budget == "low" and any("cost" in c.get("reason", "") for c in rejected_out):
        tradeoffs.append("Accepted narrower vendor features to stay within cost constraints.")
    if deploy in ("self_hosted", "on_prem"):
        tradeoffs.append("Accepted more hands-on operations in exchange for deployment control.")
    if runners_up and not tradeoffs:
        tradeoffs.append(
            f"Chose {selected_name} over other viable options that scored close on this stage."
        )

    fit_strength = _fit_strength_from_score(winner_score)
    return {
        "category": category,
        "selection_reason": selection_reason,
        "considered": considered,
        "rejected": rejected_out,
        "tradeoffs_accepted": tradeoffs,
        "operational_implications": _operational_line(category, state),
        "deployment_implications": _deployment_line(state, selected_name),
        "scaling_implications": _scaling_line(category, state),
        "workload_fit": _workload_fit_line(category, state),
        "fit_strength": fit_strength,
        "operational_risk": _operational_risk_for_category(category, state),
    }


def _fit_strength_from_score(score: float | None) -> str:
    if score is None:
        return "solid"
    if score >= 8.0:
        return "strong"
    if score >= 6.5:
        return "solid"
    return "moderate"


def _operational_risk_for_category(category: str, state: ConstraintState) -> str:
    deploy = state.get("deployment_preference") or state.get("deployment")
    if category in ("vector_databases", "llm_layer") and deploy in ("self_hosted", "on_prem"):
        return "medium"
    if category in ("workflow_orchestration", "deployment", "evaluation"):
        return "low"
    if state.get("scale") == "enterprise":
        return "medium"
    return "low"


def _operational_line(category: str, state: ConstraintState) -> str:
    if category == "vector_databases":
        return "Plan for index growth, query volume, and replication as retrieval traffic increases."
    if category == "llm_layer":
        return "Token usage and latency will dominate day-two cost — size context windows to your SLA."
    if category == "evaluation":
        return "Instrument quality early so regressions surface before end users do."
    complexity = state.get("operational_complexity_tolerance") or "medium"
    return _COMPLEXITY_LABELS.get(str(complexity), _COMPLEXITY_LABELS["medium"]) + "."


def _deployment_line(state: ConstraintState, selected_name: str) -> str:
    deploy = state.get("deployment_preference") or state.get("deployment")
    if deploy in ("self_hosted", "on_prem"):
        return f"{selected_name} aligns with self-hosted or hybrid deployment where you control infrastructure."
    if deploy in ("managed", "cloud"):
        return f"{selected_name} fits a managed deployment model to reduce operational toil."
    return f"{selected_name} should match your target deployment environment — confirm residency and networking."


def _scaling_line(category: str, state: ConstraintState) -> str:
    scale = state.get("scale")
    if category in ("vector_databases", "embeddings") and scale in (
        "enterprise",
        "growing_application",
    ):
        return "Designed to scale with document volume and concurrent retrieval load."
    if scale == "prototype":
        return "Appropriate for early workloads with a clear path to scale components later."
    return "Supports production growth when indexing, caching, and observability are planned."


def _workload_fit_line(category: str, state: ConstraintState) -> str:
    use_case = state.get("use_case")
    if use_case and str(use_case).lower() in ("rag", "qa", "question_answering"):
        if category in ("vector_databases", "retrieval", "rag_architectures"):
            return "Central to production RAG patterns with grounded answers from retrieved context."
    scale = state.get("scale")
    if scale in ("enterprise", "growing_application"):
        return "Matches medium-to-large production AI workloads with sustained query traffic."
    return "Fits a typical production AI pipeline for your current constraint profile."


def build_continuity_framing(
    state: ConstraintState,
    previous_snapshot: dict[str, Any] | None,
) -> str | None:
    """Cross-turn architectural posture when constraints are stable."""
    if not previous_snapshot:
        return None
    deploy = state.get("deployment_preference") or state.get("deployment")
    if deploy in ("self_hosted", "on_prem"):
        return "Continuing with your self-hosted infrastructure direction."
    if deploy in ("managed", "cloud"):
        return "Continuing with your preference for managed operational simplicity."
    budget = state.get("budget") or state.get("budget_tier")
    if budget == "low":
        return "Maintaining cost-conscious architecture choices across this session."
    return None


def build_evidence_hierarchy(
    trace: AdvisorTrace,
    state: ConstraintState,
    selections: dict[str, str],
) -> dict[str, Any]:
    """Ranked evidence lines for confidence storytelling."""
    items: list[dict[str, str]] = []
    deploy = state.get("deployment_preference") or state.get("deployment")
    if deploy:
        items.append({
            "tier": "primary",
            "label": "Deployment alignment",
            "detail": (
                "Your deployment preference strongly shaped which components passed filtering."
            ),
        })
    scale = state.get("scale")
    if scale in ("enterprise", "growing_application"):
        items.append({
            "tier": "primary",
            "label": "Workload scale",
            "detail": (
                "Your workload closely matches proven production retrieval and indexing patterns."
            ),
        })
    visible = user_visible_filters(trace.filtered_out)
    if visible:
        items.append({
            "tier": "supporting",
            "label": "Constraint filtering",
            "detail": (
                f"{len(visible)} alternatives were ruled out before scoring finalists."
            ),
        })
    if len(selections) >= 4:
        items.append({
            "tier": "supporting",
            "label": "Pipeline coherence",
            "detail": "Each stage was scored as part of an end-to-end RAG pipeline, not in isolation.",
        })
    budget = state.get("budget") or state.get("budget_tier")
    if budget == "low":
        items.append({
            "tier": "tradeoff",
            "label": "Cost posture",
            "detail": "Some premium options were deprioritized to protect total cost of ownership.",
        })
    return {
        "strongest": items[0]["detail"] if items else "Selections follow deterministic registry scoring.",
        "items": items[:5],
    }


def build_architecture_evolution(
    previous_panel_data: dict[str, Any] | None,
    current_nodes: list[dict[str, Any]] | None,
    current_selections: dict[str, str] | None,
    adaptation: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Diff prior blueprint vs current for evolution UX."""
    if not previous_panel_data:
        return None

    prev_selections = previous_panel_data.get("selections")
    if not isinstance(prev_selections, dict):
        prev_selections = {}
        for node in previous_panel_data.get("nodes") or []:
            if not isinstance(node, dict):
                continue
            cat = node.get("category")
            slug = node.get("slug")
            if cat and slug:
                prev_selections[str(cat)] = str(slug)

    current_selections = current_selections or {}
    prev_nodes = {
        str(n.get("slug") or n.get("id")): n
        for n in (previous_panel_data.get("nodes") or [])
        if isinstance(n, dict)
    }
    curr_nodes = {
        str(n.get("slug") or n.get("id")): n
        for n in (current_nodes or [])
        if isinstance(n, dict)
    }

    replacements: list[dict[str, str]] = []
    changed_node_ids: list[str] = []

    for stage, new_slug in current_selections.items():
        old_slug = prev_selections.get(stage)
        if not old_slug or old_slug == new_slug:
            continue
        old_node = prev_nodes.get(old_slug) or {}
        new_node = next(
            (n for n in (current_nodes or []) if isinstance(n, dict) and n.get("slug") == new_slug),
            curr_nodes.get(new_slug) or {},
        )
        replacements.append({
            "stage": stage,
            "stage_label": _CATEGORY_LABELS.get(stage, stage.replace("_", " ")),
            "from_slug": old_slug,
            "from_label": str(old_node.get("label") or old_slug),
            "to_slug": new_slug,
            "to_label": str(new_node.get("label") or new_slug),
        })
        changed_node_ids.append(stage)
        if new_slug not in changed_node_ids:
            changed_node_ids.append(new_slug)

    if not replacements and not adaptation:
        return None

    return {
        "replacements": replacements,
        "changed_node_ids": list(dict.fromkeys(changed_node_ids)),
        "summary": (
            adaptation.get("message")
            if adaptation
            else f"{len(replacements)} component(s) changed after constraint update."
        ),
    }


def build_adaptation_message(
    old_snapshot: dict[str, Any],
    state: ConstraintState,
) -> dict[str, Any] | None:
    old_slots = old_snapshot.get("slots") or old_snapshot
    if not isinstance(old_slots, dict):
        return None

    changed: list[str] = []
    labels: dict[str, str] = {
        "deployment_preference": "deployment preference",
        "deployment": "deployment model",
        "budget": "budget",
        "budget_tier": "budget",
        "scale": "scale",
        "language": "language",
        "prefer_open_source": "open source preference",
    }

    for key, slot in state.slots.items():
        old_entry = old_slots.get(key)
        old_val = old_entry.get("value") if isinstance(old_entry, dict) else old_entry
        if old_val is not None and old_val != slot.value:
            changed.append(key)

    if not changed:
        return None

    readable = [labels.get(k, k.replace("_", " ")) for k in changed[:3]]
    return {
        "changed_slots": changed,
        "message": (
            f"Architecture updated because your {' and '.join(readable)} changed — "
            "components were re-scored for the new constraint profile."
        ),
    }


def build_architecture_consulting(
    *,
    trace: AdvisorTrace,
    state: ConstraintState,
    playbook_id: str,
    selections: dict[str, str] | None = None,
    stage_decisions: dict[str, Any] | None = None,
    previous_snapshot: dict[str, Any] | None = None,
    previous_panel_data: dict[str, Any] | None = None,
    current_nodes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build architecture_consulting block for interactive_architecture panel data."""
    selections = selections or {}
    stage_decisions = stage_decisions or {}

    node_decisions: dict[str, Any] = {}
    filters_by_slug = {f.slug: f for f in trace.filtered_out}

    for category, detail in stage_decisions.items():
        if not isinstance(detail, dict):
            continue
        slug = detail.get("selected_slug") or selections.get(category)
        if not slug:
            continue
        rejected = [
            filters_by_slug[s]
            for s in detail.get("rejected_slugs") or []
            if s in filters_by_slug
        ]
        if not rejected:
            rejected = [f for f in user_visible_filters(trace.filtered_out) if f.slug != slug][:4]

        node_decisions[slug] = _build_node_decision(
            category=category,
            selected_slug=slug,
            selected_label=detail.get("selected_label") or slug,
            runners_up=detail.get("runners_up") or [],
            rejected=rejected,
            state=state,
            winner_score=detail.get("winner_score"),
        )
        node_id = detail.get("node_id") or category
        if node_id and node_id != slug:
            node_decisions[node_id] = node_decisions[slug]

    for category, slug in selections.items():
        if slug in node_decisions:
            continue
        scores_for = [r for r in trace.scores if r.slug == slug]
        winner_score = scores_for[0].score if scores_for else None
        node_decisions[slug] = _build_node_decision(
            category=category,
            selected_slug=slug,
            selected_label=slug,
            runners_up=[],
            rejected=[],
            state=state,
            winner_score=winner_score,
        )

    adaptation = None
    if previous_snapshot:
        adaptation = build_adaptation_message(previous_snapshot, state)

    evolution = build_architecture_evolution(
        previous_panel_data,
        current_nodes,
        selections,
        adaptation,
    )

    confidence = _confidence_block(trace, selections)
    evidence = build_evidence_hierarchy(trace, state, selections)
    confidence["strongest_evidence"] = evidence.get("strongest")
    confidence["evidence_hierarchy"] = evidence.get("items")

    operational = _operational_posture(state, node_decisions)
    timeline = _build_decision_timeline(
        previous_panel_data,
        evolution=evolution,
        adaptation=adaptation,
    )

    return {
        "playbook_id": playbook_id,
        "constraint_snapshot": state.slot_values(),
        "workload_framing": _workload_framing(state),
        "scale_badge": _SCALE_BADGES.get(str(state.get("scale") or ""), None),
        "scale_atmosphere": _scale_atmosphere(state),
        "operational_complexity": _COMPLEXITY_LABELS.get(
            str(state.get("operational_complexity_tolerance") or "medium"),
            _COMPLEXITY_LABELS["medium"],
        ),
        "comparative_priority_line": _comparative_priority_line(state),
        "priorities": _derive_priorities(state),
        "confidence": confidence,
        "deployment_rationale": _deployment_rationale(state),
        "scaling_rationale": _scaling_rationale(state),
        "node_decisions": node_decisions,
        "adaptation": adaptation,
        "evolution": evolution,
        "continuity_framing": build_continuity_framing(state, previous_snapshot),
        "evidence_hierarchy": evidence,
        "operational_posture": operational,
        "proactive_insights": _proactive_insights(state, trace, selections),
        "lifecycle_notes": _lifecycle_notes(state),
        "decision_timeline": timeline,
    }


def _operational_posture(
    state: ConstraintState,
    node_decisions: dict[str, Any],
) -> dict[str, Any]:
    scale = state.get("scale")
    deploy = state.get("deployment_preference") or state.get("deployment")
    risks = [d.get("operational_risk") for d in node_decisions.values() if isinstance(d, dict)]
    high_risk = sum(1 for r in risks if r == "medium")

    scaling_pressure = (
        "elevated" if scale in ("enterprise", "growing_application") else "moderate"
    )
    maintenance = "higher" if deploy in ("self_hosted", "on_prem") else "moderate"
    observability = "plan early" if scale != "prototype" else "lightweight for now"
    production_ready = (
        "production-grade posture"
        if scale in ("enterprise", "growing_application")
        else "growth-ready with planned hardening"
    )

    return {
        "scaling_pressure": scaling_pressure,
        "maintenance_complexity": maintenance,
        "deployment_burden": "self-managed" if deploy in ("self_hosted", "on_prem") else "managed-leaning",
        "operational_risk": "medium" if high_risk >= 2 else "low",
        "observability_maturity": observability,
        "production_readiness": production_ready,
    }


def _proactive_insights(
    state: ConstraintState,
    trace: AdvisorTrace,
    selections: dict[str, str],
) -> list[str]:
    insights: list[str] = []
    scale = state.get("scale")
    deploy = state.get("deployment_preference") or state.get("deployment")

    if scale in ("growing_application", "enterprise"):
        insights.append(
            "At projected scale, retrieval index capacity and query concurrency deserve early capacity planning."
        )
    if deploy in ("self_hosted", "on_prem"):
        insights.append(
            "Self-hosted components may require operational automation as your team and traffic grow."
        )
    if "vector_databases" in selections and scale != "prototype":
        insights.append(
            "You may eventually evaluate sharding or replication if document volume outpaces single-node limits."
        )
    if state.get("latency_priority") == "critical":
        insights.append(
            "Latency-critical workloads often benefit from caching and reranking tuning before scaling hardware."
        )
    if len(trace.filtered_out) > 5:
        insights.append(
            "Several alternatives were filtered by constraints — revisiting budget or deployment slots can reopen options."
        )
    if not insights:
        insights.append(
            "Monitor embedding and retrieval costs as usage grows; they typically dominate RAG operational spend."
        )
    return insights[:4]


def _lifecycle_notes(state: ConstraintState) -> list[str]:
    notes: list[str] = []
    scale = state.get("scale")
    if scale == "prototype":
        notes.append(
            "Current posture favors iteration speed; plan a retrieval and observability hardening phase before enterprise traffic."
        )
    elif scale == "growing_application":
        notes.append(
            "As traffic increases, reranking latency and index rebuild windows often become the first bottlenecks."
        )
    elif scale == "enterprise":
        notes.append(
            "At enterprise scale, managed retrieval costs and operational governance may push toward dedicated platform teams."
        )
    deploy = state.get("deployment_preference") or state.get("deployment")
    if deploy in ("managed", "cloud"):
        notes.append(
            "Managed services reduce day-two burden but can create vendor coupling — document migration paths early."
        )
    return notes[:3]


def _build_decision_timeline(
    previous_panel_data: dict[str, Any] | None,
    *,
    evolution: dict[str, Any] | None,
    adaptation: dict[str, Any] | None,
) -> list[dict[str, str]]:
    timeline: list[dict[str, str]] = []
    if previous_panel_data:
        prior = previous_panel_data.get("architecture_consulting") or {}
        existing = prior.get("decision_timeline")
        if isinstance(existing, list):
            timeline.extend(existing[-4:])

    if evolution and evolution.get("replacements"):
        for rep in evolution["replacements"][:2]:
            timeline.append({
                "type": "component_change",
                "title": rep.get("stage_label", "Stage"),
                "detail": f"{rep.get('from_label')} replaced by {rep.get('to_label')}",
            })
    elif adaptation:
        timeline.append({
            "type": "constraint_shift",
            "title": "Constraints updated",
            "detail": adaptation.get("message", "Architecture re-scored"),
        })

    return timeline[-6:]


def _scale_atmosphere(state: ConstraintState) -> str:
    scale = str(state.get("scale") or "")
    if scale == "enterprise":
        return "enterprise"
    if scale in ("growing_application", "medium"):
        return "production"
    if scale in ("prototype", "small"):
        return "prototype"
    return "production"


def _derive_priorities(state: ConstraintState) -> list[str]:
    priorities: list[str] = []
    deploy = state.get("deployment_preference") or state.get("deployment")
    if deploy in ("managed", "cloud"):
        priorities.append("Managed deployment and operational simplicity")
    elif deploy in ("self_hosted", "on_prem"):
        priorities.append("Deployment control and data residency")
    budget = state.get("budget") or state.get("budget_tier")
    if budget == "low":
        priorities.append("Cost-efficient operations")
    scale = state.get("scale")
    if scale in ("enterprise", "growing_application"):
        priorities.append("Scalable semantic retrieval")
    if state.get("language") == "python":
        priorities.append("Python-friendly integration")
    if not priorities:
        priorities.append("Coherent end-to-end pipeline design")
    return priorities[:4]


def _deployment_rationale(state: ConstraintState) -> str:
    deploy = state.get("deployment_preference") or state.get("deployment")
    if deploy in ("self_hosted", "on_prem"):
        return "Deployment choices favor infrastructure you can run and audit under your own policies."
    if deploy in ("managed", "cloud"):
        return "Deployment choices favor managed services to reduce day-two operational burden."
    return "Deployment should be validated against your residency, networking, and ops model."


def _scaling_rationale(state: ConstraintState) -> str:
    scale = state.get("scale")
    if scale == "enterprise":
        return "Architecture assumes enterprise-scale retrieval volume and team operational maturity."
    if scale == "growing_application":
        return "Architecture assumes growing document and query volume with room to scale indexes and workers."
    if scale == "prototype":
        return "Architecture supports rapid iteration with a path to harden for production scale."
    return "Architecture targets sustained production usage with moderate growth headroom."
