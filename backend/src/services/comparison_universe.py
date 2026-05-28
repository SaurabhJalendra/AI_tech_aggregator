"""Comparison universe — same-abstraction-layer shortlists only."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from src.models.module import Module
from src.schemas.constraint_state import ConstraintSource, ConstraintState

_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "advisor_registry" / "comparison_universe.yaml"


@lru_cache(maxsize=1)
def _load_universe() -> dict[str, Any]:
    if not _REGISTRY_PATH.exists():
        return {}
    raw = yaml.safe_load(_REGISTRY_PATH.read_text(encoding="utf-8"))
    return raw.get("categories") or {}


def list_layers_for_category(category: str) -> dict[str, dict[str, Any]]:
    cat = _load_universe().get(category) or {}
    layers = cat.get("layers") or {}
    return {str(k): v for k, v in layers.items() if isinstance(v, dict)}


def get_layer_slugs(category: str, layer: str) -> frozenset[str]:
    layers = list_layers_for_category(category)
    layer_def = layers.get(layer) or {}
    slugs = layer_def.get("module_slugs") or []
    return frozenset(str(s) for s in slugs)


def get_layer_label(category: str, layer: str) -> str:
    layers = list_layers_for_category(category)
    layer_def = layers.get(layer) or {}
    return str(layer_def.get("label") or layer.replace("_", " "))


def resolve_comparison_layer(
    category: str,
    message: str,
    state: ConstraintState | None = None,
    client_context: dict | None = None,
) -> str | None:
    """Pick comparison layer for a category; None if category has no universe rules."""
    cat = _load_universe().get(category)
    if not cat:
        return None

    if state and state.get("comparison_layer"):
        return str(state.get("comparison_layer"))

    if client_context:
        ctx_layer = client_context.get("comparison_layer")
        if ctx_layer:
            return str(ctx_layer)
        cs = client_context.get("constraint_state")
        if isinstance(cs, dict):
            slots = cs.get("slots") or {}
            slot = slots.get("comparison_layer")
            if isinstance(slot, dict) and slot.get("value"):
                return str(slot["value"])

    combined = message.lower()
    if client_context and client_context.get("active_task"):
        combined = f"{client_context['active_task']} {combined}".lower()

    keywords: dict[str, list[str]] = cat.get("layer_keywords") or {}
    for layer, terms in keywords.items():
        if any(term in combined for term in terms):
            return layer

    default = cat.get("default_layer")
    return str(default) if default else None


def _layer_definition(category: str, layer: str) -> dict[str, Any]:
    return list_layers_for_category(category).get(layer) or {}


def filter_modules_by_layer(
    modules: list[Module],
    category: str,
    layer: str,
) -> tuple[list[Module], list[str]]:
    """Keep only modules in the canonical comparison layer (subcategory or slug whitelist)."""
    layer_def = _layer_definition(category, layer)
    subcategory = layer_def.get("subcategory")
    if subcategory:
        target = str(subcategory)
        kept = [m for m in modules if (m.subcategory or "") == target]
        removed = [m.slug for m in modules if (m.subcategory or "") != target]
        return kept, removed

    allowed = get_layer_slugs(category, layer)
    if not allowed:
        return modules, []
    kept = [m for m in modules if m.slug in allowed]
    removed = [m.slug for m in modules if m.slug not in allowed]
    return kept, removed


def apply_comparison_layer_to_state(
    state: ConstraintState,
    category: str,
    layer: str,
) -> None:
    state.set_slot(
        "comparison_layer",
        layer,
        source=ConstraintSource.INFERRED,
        confidence=0.9,
    )
    state.set_slot(
        "comparison_layer_label",
        get_layer_label(category, layer),
        source=ConstraintSource.INFERRED,
        confidence=0.9,
    )
