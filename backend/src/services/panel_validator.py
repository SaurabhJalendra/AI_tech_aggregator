"""Validate and gate panel commands (planner authority)."""

from __future__ import annotations

from typing import Any

ALLOWED_PANELS = frozenset({
    "welcome",
    "architecture_diagram",
    "comparison_table",
    "comparison_chart",
    "code_preview",
    "module_detail",
    "recommendation",
    "document",
    "option_cards",
    "interactive_architecture",
    "code_project",
})

ALLOWED_ACTIONS = frozenset({"render", "update", "clear"})

# Panels the LLM may emit only when no active deterministic playbook is running.
LLM_RESTRICTED_PANELS = frozenset({
    "comparison_chart",
    "comparison_table",
    "option_cards",
    "interactive_architecture",
})


def validate_panel_command(command: dict[str, Any]) -> tuple[bool, str | None]:
    """Return (ok, error_message)."""
    if not isinstance(command, dict):
        return False, "command must be a dict"

    action = command.get("action")
    panel = command.get("panel")
    data = command.get("data")

    if action not in ALLOWED_ACTIONS:
        return False, f"invalid action: {action!r}"
    if panel not in ALLOWED_PANELS:
        return False, f"invalid panel: {panel!r}"
    if action in ("render", "update") and not isinstance(data, dict):
        return False, "data must be a dict for render/update"

    if panel == "option_cards" and action == "render":
        qid = data.get("question_id") if isinstance(data, dict) else None
        options = data.get("options") if isinstance(data, dict) else None
        if not qid or not isinstance(options, list) or len(options) < 2:
            return False, "option_cards requires question_id and options"

    return True, None


def filter_llm_panel_command(
    command: dict[str, Any],
    *,
    active_playbook_id: str | None,
    planner_authority_strict: bool,
    has_deterministic_evidence: bool = False,
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Drop or allow LLM-originated panel commands under planner authority rules.
    Returns (command_or_none, drop_reason).
    """
    ok, err = validate_panel_command(command)
    if not ok:
        return None, err

    if has_deterministic_evidence:
        return None, "LLM cannot emit panels when deterministic recommendation evidence exists"

    if not planner_authority_strict:
        return command, None

    if not active_playbook_id:
        return command, None

    panel = command.get("panel")
    if panel in LLM_RESTRICTED_PANELS:
        return None, f"LLM cannot emit panel {panel!r} while playbook {active_playbook_id} is active"

    if planner_authority_strict:
        return None, f"LLM cannot emit panel {panel!r} under strict planner authority"

    return command, None
