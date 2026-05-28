"""Load and resolve declarative advisor playbooks."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_PLAYBOOKS_PATH = Path(__file__).resolve().parent / "playbooks.yaml"


@lru_cache(maxsize=1)
def _load_raw() -> dict[str, Any]:
    raw = yaml.safe_load(_PLAYBOOKS_PATH.read_text(encoding="utf-8"))
    return raw.get("playbooks") or {}


def list_playbooks() -> dict[str, dict[str, Any]]:
    return dict(_load_raw())


def get_playbook(playbook_id: str) -> dict[str, Any] | None:
    playbook = _load_raw().get(playbook_id)
    if not isinstance(playbook, dict):
        return None
    return playbook


def get_playbook_by_intent(intent_id: str) -> dict[str, Any] | None:
    for playbook_id, playbook in _load_raw().items():
        intent_ids = playbook.get("intent_ids") or []
        if intent_id in intent_ids:
            return {"playbook_id": playbook_id, **playbook}
    return None


def get_playbook_by_task_type(task_type: str, category: str | None = None) -> dict[str, Any] | None:
    for playbook_id, playbook in _load_raw().items():
        if playbook.get("task_type") != task_type:
            continue
        if category and playbook.get("category") and playbook.get("category") != category:
            continue
        return {"playbook_id": playbook_id, **playbook}
    return None


def resolve_playbook_id(
    intent_id: str | None = None,
    task_type: str | None = None,
    category: str | None = None,
) -> str | None:
    if intent_id:
        match = get_playbook_by_intent(intent_id)
        if match:
            return str(match["playbook_id"])
    if task_type:
        match = get_playbook_by_task_type(task_type, category)
        if match:
            return str(match["playbook_id"])
    return None


def playbook_required_slots(playbook_id: str) -> list[str]:
    playbook = get_playbook(playbook_id)
    if not playbook:
        return []
    slots = playbook.get("required_slots") or []
    return [str(s) for s in slots]


def playbook_slot_impact_values(playbook_id: str) -> dict[str, list[str]]:
    """Enumerated values for impact-aware slot simulation (from playbooks.yaml)."""
    playbook = get_playbook(playbook_id)
    if not playbook:
        return {}
    raw = playbook.get("slot_impact_values") or {}
    return {str(k): [str(v) for v in vals] for k, vals in raw.items() if isinstance(vals, list)}
