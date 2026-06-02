"""Reusable paraphrase regression fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_FIXTURES_PATH = Path(__file__).resolve().parent / "paraphrase_groups.yaml"


def load_paraphrase_groups() -> list[dict[str, Any]]:
    raw = yaml.safe_load(_FIXTURES_PATH.read_text(encoding="utf-8"))
    groups = raw.get("groups") or {}
    out: list[dict[str, Any]] = []
    for group_id, group in groups.items():
        if not isinstance(group, dict):
            continue
        out.append({"group_id": group_id, **group})
    return out


def load_vector_db_shortlist_snapshot() -> dict[str, Any]:
    raw = yaml.safe_load(_FIXTURES_PATH.read_text(encoding="utf-8"))
    return raw.get("vector_db_shortlist_snapshot") or {}
