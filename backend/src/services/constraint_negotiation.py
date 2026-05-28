"""Deterministic negotiation when hard filters exclude all candidates."""

from __future__ import annotations

from collections import Counter

from src.schemas.advisor_trace import AdvisorTrace, FilterRecord
from src.schemas.constraint_state import ConstraintState


_RELAXATION_RULES: list[tuple[str, str, str, dict[str, str]]] = [
    (
        "deployment_preference",
        "Relax deployment requirement",
        "Try managed cloud or hybrid deployment instead of strict self-hosted.",
        {"deployment_preference": "managed"},
    ),
    (
        "budget",
        "Relax budget constraint",
        "Allow medium-tier options if lowest-cost filters removed all finalists.",
        {"budget": "medium"},
    ),
    (
        "persistence_required",
        "Relax persistence requirement",
        "Compare options that do not require durable on-disk persistence.",
        {"persistence_required": False},
    ),
    (
        "open_source_only",
        "Relax open-source requirement",
        "Include commercially licensed options that still fit your scale.",
        {"open_source_only": False},
    ),
]


def _dominant_filter_themes(filtered_out: list[FilterRecord]) -> Counter[str]:
    themes: Counter[str] = Counter()
    for record in filtered_out:
        reason = record.reason.lower()
        if "deployment" in reason or "self_hosted" in reason or "managed" in reason:
            themes["deployment_preference"] += 1
        if "budget" in reason or "pricing" in reason or "cost" in reason:
            themes["budget"] += 1
        if "persistence" in reason:
            themes["persistence_required"] += 1
        if "open" in reason and "source" in reason:
            themes["open_source_only"] += 1
    return themes


def build_negotiation_option_cards(
    state: ConstraintState,
    trace: AdvisorTrace,
    *,
    playbook_id: str = "vector_db_comparison",
) -> dict:
    """Option-card payload suggesting deterministic constraint relaxations."""
    themes = _dominant_filter_themes(trace.filtered_out)
    active_constraints = [
        f"{key}={state.get(key)}"
        for key in ("budget", "deployment_preference", "persistence_required", "open_source_only")
        if state.has(key)
    ]
    constraint_summary = ", ".join(active_constraints) or "your current filters"

    options: list[dict] = []
    for slot, label, description, metadata in _RELAXATION_RULES:
        if state.has(slot) and (themes[slot] > 0 or not themes):
            options.append(
                {
                    "id": f"relax_{slot}",
                    "label": label,
                    "description": description,
                    "icon": "split",
                    "metadata": metadata,
                }
            )
        if len(options) >= 3:
            break

    if not options:
        options = [
            {
                "id": "relax_budget",
                "label": "Relax budget constraint",
                "description": "Broaden cost tier to surface more finalists.",
                "icon": "coin",
                "metadata": {"budget": "medium"},
            },
            {
                "id": "relax_deployment",
                "label": "Relax deployment requirement",
                "description": "Allow managed or hybrid deployment models.",
                "icon": "cloud",
                "metadata": {"deployment_preference": "managed"},
            },
        ]

    question = (
        f"No options satisfy all of: {constraint_summary}. "
        "Which constraint should we relax first to continue the comparison?"
    )

    return {
        "question_id": "constraint_negotiation",
        "question": question,
        "options": options,
        "negotiation": {
            "playbook_id": playbook_id,
            "filter_exhausted": True,
            "filtered_count": len(trace.filtered_out),
            "constraint_snapshot": state.slot_values(),
        },
    }
