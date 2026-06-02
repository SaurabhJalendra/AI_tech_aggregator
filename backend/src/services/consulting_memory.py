"""Cross-session strategic consulting memory."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

MAX_PINNED_STRATEGIES = 5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.consulting import ArchitectureEvolutionSnapshot
from src.models.user import User
from src.schemas.constraint_state import ConstraintState

PROFILE_SLOTS = (
    "deployment_preference",
    "deployment",
    "budget",
    "budget_tier",
    "scale",
    "operational_complexity_tolerance",
    "prefer_open_source",
    "latency_priority",
    "implementation_preference",
    "data_sensitivity",
    "infrastructure_direction",
)

DIRECTION_LABELS = {
    "managed": "managed operational simplicity",
    "self_hosted": "self-hosted control and data residency",
    "hybrid": "hybrid deployment flexibility",
    "cost_conscious": "cost-conscious infrastructure choices",
    "scale_ready": "scale-ready retrieval and serving patterns",
    "low_ops": "low operational toil",
}


def _slot_value(state: ConstraintState | dict[str, Any], key: str) -> Any:
    if isinstance(state, ConstraintState):
        return state.get(key)
    slots = state.get("slots") if isinstance(state, dict) else None
    if isinstance(slots, dict) and key in slots:
        slot = slots[key]
        if isinstance(slot, dict):
            return slot.get("value")
    return state.get(key) if isinstance(state, dict) else None


def merge_profile_from_state(profile: dict[str, Any], state: ConstraintState) -> dict[str, Any]:
    """Accumulate strategic slots from the latest constraint state."""
    out = dict(profile or {})
    slots_out: dict[str, Any] = dict(out.get("slots") or {})
    for key in PROFILE_SLOTS:
        val = _slot_value(state, key)
        if val is None or val == "":
            continue
        slots_out[key] = {
            "value": val,
            "updated_at": out.get("last_updated"),
            "source": "session",
        }
    out["slots"] = slots_out
    out["infrastructure_direction"] = _infer_direction(slots_out)
    return out


def _infer_direction(slots: dict[str, Any]) -> str | None:
    deploy = _read_slot(slots, "deployment_preference") or _read_slot(slots, "deployment")
    budget = _read_slot(slots, "budget") or _read_slot(slots, "budget_tier")
    scale = _read_slot(slots, "scale")
    tolerance = _read_slot(slots, "operational_complexity_tolerance")

    if deploy in ("managed", "cloud"):
        return "managed"
    if deploy in ("self_hosted", "on_prem"):
        if budget == "low":
            return "cost_conscious"
        return "self_hosted"
    if scale in ("enterprise", "growing_application"):
        return "scale_ready"
    if tolerance == "low":
        return "low_ops"
    return None


def _read_slot(slots: dict[str, Any], key: str) -> Any:
    entry = slots.get(key)
    if isinstance(entry, dict):
        return entry.get("value")
    return entry


def apply_profile_to_context(profile: dict[str, Any] | None, client_context: dict) -> None:
    """Inject consulting memory into client_context for planner + UI."""
    if not profile:
        return
    client_context["consulting_profile"] = profile
    framing = build_continuity_framing(profile)
    if framing:
        client_context["consulting_continuity"] = framing


def build_continuity_framing(profile: dict[str, Any]) -> str | None:
    """Human line for cross-session consulting relationship."""
    direction = profile.get("infrastructure_direction")
    if direction and direction in DIRECTION_LABELS:
        return (
            f"Continuing your consulting engagement — you've been steering toward "
            f"{DIRECTION_LABELS[direction]}."
        )
    slots = profile.get("slots") or {}
    deploy = _read_slot(slots, "deployment_preference") or _read_slot(slots, "deployment")
    if deploy in ("managed", "cloud"):
        return "Continuing with your preference for managed operational simplicity."
    if deploy in ("self_hosted", "on_prem"):
        return "Continuing with your self-hosted infrastructure direction."
    budget = _read_slot(slots, "budget") or _read_slot(slots, "budget_tier")
    if budget == "low":
        return "Maintaining your cost-conscious infrastructure posture across sessions."
    return None


async def load_user_profile(db: AsyncSession, user: User) -> dict[str, Any]:
    """Load consulting profile by user id (safe during SSE streaming)."""
    result = await db.execute(
        select(User.consulting_profile).where(User.id == user.id)
    )
    raw = result.scalar_one_or_none()
    return dict(raw or {})


async def persist_user_profile(
    db: AsyncSession,
    user: User,
    profile: dict[str, Any],
) -> None:
    """Persist profile without requiring a session-attached User instance."""
    row = await db.get(User, user.id)
    if row is None:
        return
    row.consulting_profile = profile
    await db.flush()


async def record_evolution_snapshot(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID | None,
    title: str,
    summary: str | None,
    selections: dict[str, str],
    nodes: list[dict[str, Any]],
    constraint_snapshot: dict[str, Any],
    transition_reason: str | None = None,
) -> ArchitectureEvolutionSnapshot:
    row = ArchitectureEvolutionSnapshot(
        user_id=user_id,
        conversation_id=conversation_id,
        title=title[:300],
        summary=summary,
        selections=selections or {},
        nodes_snapshot=nodes[:40],
        constraint_snapshot=constraint_snapshot or {},
        transition_reason=transition_reason,
    )
    db.add(row)
    await db.flush()
    return row


def get_pinned_strategies(profile: dict[str, Any]) -> list[dict[str, Any]]:
    workspace = profile.get("strategy_workspace") or {}
    return list(workspace.get("pinned") or [])


def pin_current_architecture(
    profile: dict[str, Any],
    *,
    title: str,
    panel_data: dict[str, Any],
    constraint_snapshot: dict[str, Any],
) -> dict[str, Any]:
    """Pin an architecture future to the strategy workspace."""
    out = dict(profile or {})
    workspace = dict(out.get("strategy_workspace") or {})
    pinned = list(workspace.get("pinned") or [])
    entry = {
        "id": str(uuid.uuid4()),
        "title": (title or "Architecture strategy")[:200],
        "selections": panel_data.get("selections") or {},
        "nodes": (panel_data.get("nodes") or [])[:24],
        "constraint_snapshot": constraint_snapshot,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }
    pinned = [entry] + [p for p in pinned if p.get("title") != entry["title"]]
    workspace["pinned"] = pinned[:MAX_PINNED_STRATEGIES]
    out["strategy_workspace"] = workspace
    return out


def remove_pinned_strategy(profile: dict[str, Any], pin_id: str) -> dict[str, Any]:
    out = dict(profile or {})
    workspace = dict(out.get("strategy_workspace") or {})
    pinned = [p for p in (workspace.get("pinned") or []) if p.get("id") != pin_id]
    workspace["pinned"] = pinned
    out["strategy_workspace"] = workspace
    return out


async def list_evolution_history(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    limit: int = 15,
) -> list[dict[str, Any]]:
    result = await db.execute(
        select(ArchitectureEvolutionSnapshot)
        .where(ArchitectureEvolutionSnapshot.user_id == user_id)
        .order_by(ArchitectureEvolutionSnapshot.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "title": r.title,
            "summary": r.summary,
            "selections": r.selections,
            "transition_reason": r.transition_reason,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
