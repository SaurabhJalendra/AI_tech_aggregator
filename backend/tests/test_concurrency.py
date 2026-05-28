"""Concurrency safety for validation and metrics."""

import asyncio

import pytest

from src.schemas.client_context import validate_client_context
from src.services.planner_metrics import record_turn, reset, snapshot


@pytest.mark.asyncio
async def test_parallel_client_context_validation_isolated():
    async def validate_one(i: int):
        raw = {
            "active_task": f"task-{i}",
            "constraint_state": {
                "slots": {f"slot_{i}": {"value": i, "source": "explicit", "confidence": 1}},
                "version": "1",
            },
        }
        safe, stats = validate_client_context(raw)
        return safe.get("active_task"), stats.total_chars

    results = await asyncio.gather(*[validate_one(i) for i in range(20)])
    tasks = {r[0] for r in results}
    assert len(tasks) == 20


def test_planner_metrics_no_cross_session_leakage():
    reset()
    for i in range(10):
        record_turn({"planner_mode": "on", "intercepted": i % 2 == 0, "session_turn_index": i})
    snap = snapshot()
    assert snap["turns_total"] == 10
    reset()
    assert snapshot()["turns_total"] == 0


def test_legacy_flat_constraints_rejected():
    safe, stats = validate_client_context({
        "active_task": "compare",
        "constraints": {"budget": "low"},
        "constraint_state": {"slots": {}, "version": "1"},
    })
    assert stats.flat_constraints_rejected == 1
    assert "constraints" not in safe
