"""Tests for declarative playbook loader."""

from src.advisor_playbooks.loader import (
    get_playbook,
    get_playbook_by_intent,
    playbook_required_slots,
    resolve_playbook_id,
)


def test_resolve_vector_db_playbook():
    assert resolve_playbook_id(intent_id="category:vector_databases") == "vector_db_comparison"


def test_vector_db_required_slots():
    slots = playbook_required_slots("vector_db_comparison")
    assert slots == ["budget", "scale", "deployment_preference"]


def test_rag_pipeline_playbook():
    pb = get_playbook_by_intent("rag_pipeline")
    assert pb is not None
    assert pb["playbook_id"] == "rag_pipeline_design"
    assert pb["task_type"] == "rag_pipeline"


def test_module_code_playbook_has_no_required_slots():
    pb = get_playbook("module_code")
    assert pb is not None
    assert pb.get("required_slots") == []
