"""Tests for panel command validation and LLM gating."""

from src.services.panel_validator import filter_llm_panel_command, validate_panel_command


def test_validate_option_cards_requires_options():
    ok, err = validate_panel_command({
        "action": "render",
        "panel": "option_cards",
        "data": {"question_id": "budget"},
    })
    assert not ok
    assert "options" in (err or "")


def test_llm_comparison_chart_blocked_under_active_playbook():
    cmd, reason = filter_llm_panel_command(
        {
            "action": "render",
            "panel": "comparison_chart",
            "data": {"comparison": {}},
        },
        active_playbook_id="vector_db_comparison",
        planner_authority_strict=True,
    )
    assert cmd is None
    assert reason is not None


def test_llm_code_preview_allowed_under_playbook():
    cmd, reason = filter_llm_panel_command(
        {
            "action": "render",
            "panel": "code_preview",
            "data": {"code": "print(1)"},
        },
        active_playbook_id="vector_db_comparison",
        planner_authority_strict=True,
    )
    assert cmd is not None
    assert reason is None
