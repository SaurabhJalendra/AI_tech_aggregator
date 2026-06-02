"""Unified decision metadata: YAML overlays + module technical_specs.decision."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from src.models.module import Module

_REGISTRY_DIR = Path(__file__).resolve().parent.parent / "advisor_registry"


@lru_cache(maxsize=1)
def _load_yaml_overlays() -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for name in ("vector_databases_decision.yaml", "rag_modules_decision.yaml"):
        path = _REGISTRY_DIR / name
        if path.exists():
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            modules = raw.get("modules") or {}
            for slug, meta in modules.items():
                if isinstance(meta, dict):
                    merged[str(slug)] = dict(meta)
    return merged


def get_decision_metadata(slug: str, module: Module | None = None) -> dict[str, Any]:
    """Resolve metadata: module.spec decision block overrides YAML overlay."""
    overlay = _load_yaml_overlays().get(slug, {})
    if module is None:
        return dict(overlay)
    specs = module.technical_specs if isinstance(module.technical_specs, dict) else {}
    decision = specs.get("decision")
    if isinstance(decision, dict) and decision:
        merged = dict(overlay)
        merged.update(decision)
        return merged
    return dict(overlay)


def decision_from_comparison_dimensions(comparison_dims: dict) -> dict[str, Any]:
    """Baseline decision block from module spec comparison_dimensions (no advisor overlay)."""
    scores: dict[str, Any] = {}
    for dim, data in (comparison_dims or {}).items():
        if isinstance(data, dict) and "score" in data:
            scores[dim] = data["score"]
    if not scores:
        return {}
    return {"source": "module_spec", "comparison_scores": scores}


def merge_overlay_into_technical_specs(spec: dict) -> dict:
    """Merge advisor overlay + spec decision + comparison fallback into technical_specs."""
    slug = spec.get("meta", {}).get("slug")
    technical = dict(spec.get("technical_specs") or {})
    overlay = _load_yaml_overlays().get(slug or "", {}) if slug else {}
    existing = technical.get("decision")
    if isinstance(existing, dict):
        merged_decision: dict[str, Any] = dict(existing)
    else:
        merged_decision = {}

    if overlay:
        merged_decision = {**overlay, **merged_decision}

    if not merged_decision:
        derived = decision_from_comparison_dimensions(spec.get("comparison_dimensions") or {})
        if derived:
            merged_decision = derived

    if merged_decision:
        technical["decision"] = merged_decision
    return technical


def apply_decision_metadata_to_module(module: Module, spec: dict | None = None) -> bool:
    """
    Persist canonical decision metadata on module.technical_specs.
    Returns True when the DB row should be flushed.
    """
    if spec is not None:
        technical = merge_overlay_into_technical_specs(spec)
    else:
        overlay = _load_yaml_overlays().get(module.slug, {})
        technical = dict(module.technical_specs) if isinstance(module.technical_specs, dict) else {}
        existing = technical.get("decision")
        if isinstance(existing, dict):
            merged: dict[str, Any] = dict(existing)
        else:
            merged = {}
        if overlay:
            merged = {**overlay, **merged}
        if merged:
            technical["decision"] = merged
        else:
            return False

    if technical == (module.technical_specs or {}):
        return False
    module.technical_specs = technical
    return True


def overlay_slugs() -> set[str]:
    return set(_load_yaml_overlays().keys())
