"""Shared deterministic pipeline runtime helpers."""

from __future__ import annotations

from src.schemas.advisor_trace import ScoreRecord


def deterministic_score_key(record: ScoreRecord) -> tuple:
    """Stable ordering: score, confidence, retrieval, slug (all rounded)."""
    return (
        -round(float(record.score), 6),
        -round(float(record.confidence), 6),
        -round(float(record.retrieval_score), 6),
        record.slug,
    )


def sort_scored_records(records: list[ScoreRecord]) -> list[ScoreRecord]:
    """Deterministic ordering across pipelines."""
    return sorted(records, key=deterministic_score_key)


def build_shortlist(
    records: list[ScoreRecord],
    *,
    limit: int,
) -> list[str]:
    return [r.slug for r in sort_scored_records(records)[:limit]]
