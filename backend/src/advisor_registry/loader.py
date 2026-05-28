"""Load Phase-2 decision metadata overlays (delegates to unified decision_metadata)."""

from __future__ import annotations

from typing import Any

from src.services.decision_metadata import _load_yaml_overlays, get_decision_metadata


def get_vector_db_decision_metadata() -> dict[str, dict[str, Any]]:
    return _load_yaml_overlays()


def get_rag_decision_metadata() -> dict[str, dict[str, Any]]:
    return _load_yaml_overlays()


def get_category_decision_metadata() -> dict[str, dict[str, Any]]:
    return _load_yaml_overlays()


def get_module_decision_metadata(slug: str) -> dict[str, Any]:
    return get_decision_metadata(slug)
