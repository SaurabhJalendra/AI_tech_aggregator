"""Declarative advisor playbooks (Phase-1 metadata layer)."""

from src.advisor_playbooks.loader import (
    get_playbook,
    get_playbook_by_intent,
    get_playbook_by_task_type,
    list_playbooks,
    playbook_required_slots,
    resolve_playbook_id,
)

__all__ = [
    "get_playbook",
    "get_playbook_by_intent",
    "get_playbook_by_task_type",
    "list_playbooks",
    "playbook_required_slots",
    "resolve_playbook_id",
]
