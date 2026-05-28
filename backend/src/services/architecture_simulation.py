"""Deterministic architecture scenario simulation (Phase-4 + semantic routing)."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from src.schemas.constraint_state import ConstraintSource, ConstraintState
from src.schemas.intent import IntentResult

logger = logging.getLogger(__name__)

SEMANTIC_SIMULATION_INTENTS: dict[str, tuple[dict[str, Any], str]] = {
    "architecture_simulation:traffic": (
        {"scale": "growing_application", "latency_priority": "critical"},
        "Higher traffic and retrieval load",
    ),
    "architecture_simulation:enterprise_scale": (
        {"scale": "enterprise"},
        "Enterprise-scale workload",
    ),
    "architecture_simulation:latency": (
        {"latency_priority": "critical"},
        "Latency becomes the top priority",
    ),
    "architecture_simulation:managed": (
        {"deployment_preference": "managed"},
        "Managed cloud deployment preference",
    ),
    "architecture_simulation:self_hosted": (
        {"deployment_preference": "self_hosted"},
        "Self-hosted deployment preference",
    ),
    "architecture_simulation:budget_up": (
        {"budget": "high"},
        "Higher budget tolerance",
    ),
    "architecture_simulation:budget_down": (
        {"budget": "low"},
        "Tighter cost constraints",
    ),
    "architecture_simulation:privacy": (
        {"deployment_preference": "self_hosted", "data_sensitivity": "high"},
        "Stricter privacy and data control",
    ),
    "architecture_simulation:compliance": (
        {"data_sensitivity": "high", "deployment_preference": "self_hosted"},
        "Tightening compliance and residency (e.g. regional expansion)",
    ),
    "architecture_simulation:throughput_imbalance": (
        {"scale": "growing_application", "latency_priority": "critical"},
        "Retrieval throughput outpacing embedding generation",
    ),
    "architecture_simulation:platform_capacity": (
        {"operational_complexity_tolerance": "low", "deployment_preference": "managed"},
        "Limited platform engineering capacity",
    ),
    "architecture_simulation:observability_overhead": (
        {"scale": "growing_application", "operational_complexity_tolerance": "medium"},
        "Observability overhead becoming difficult to manage",
    ),
    "architecture_simulation:hybrid": (
        {"deployment_preference": "hybrid", "scale": "growing_application"},
        "Shift toward hybrid cloud-native posture",
    ),
}

_SIMULATION_PATTERNS: list[tuple[str, dict[str, Any], str]] = [
    (
        r"what if.{0,40}(10x|ten times|traffic|query volume|load).{0,30}(increas|grow|double|10)",
        {"scale": "growing_application"},
        "Higher traffic and query volume",
    ),
    (
        r"what if.{0,50}(enterprise|production scale|at scale)",
        {"scale": "enterprise"},
        "Enterprise-scale workload",
    ),
    (
        r"what if.{0,40}(prototype|early).{0,30}(enterprise|production)",
        {"scale": "enterprise"},
        "Prototype to enterprise scale transition",
    ),
    (
        r"what if.{0,50}(latency|speed|response time).{0,30}(critical|important|matters|sla)",
        {"latency_priority": "critical"},
        "Latency becomes the top priority",
    ),
    (
        r"what if.{0,50}(self[- ]?host|on[- ]?prem|our own infra)",
        {"deployment_preference": "self_hosted"},
        "Self-hosted deployment preference",
    ),
    (
        r"what if.{0,50}(managed|cloud|fully managed)",
        {"deployment_preference": "managed"},
        "Managed cloud deployment preference",
    ),
    (
        r"what if.{0,50}(budget|cost|gpu).{0,30}(increas|higher|double)",
        {"budget": "high"},
        "Higher budget tolerance",
    ),
    (
        r"what if.{0,50}(budget|cost).{0,30}(tight|lower|reduc|cut)",
        {"budget": "low"},
        "Tighter cost constraints",
    ),
    (
        r"what if.{0,50}(privacy|compliance|residency|gdpr|hipaa)",
        {"deployment_preference": "self_hosted", "data_sensitivity": "high"},
        "Stricter privacy and data control",
    ),
    (
        r"what if.{0,50}open source",
        {"prefer_open_source": True},
        "Stronger open-source preference",
    ),
]


@dataclass
class ArchitectureSimulationSpec:
    scenario_id: str
    label: str
    slot_updates: dict[str, Any]
    user_message_excerpt: str


def simulation_from_intent(intent_result: IntentResult | None) -> ArchitectureSimulationSpec | None:
    """Map semantic intent classification to a simulation spec."""
    if intent_result is None:
        return None
    intent_id = intent_result.intent_id or ""
    if not intent_id.startswith("architecture_simulation:"):
        return None
    mapping = SEMANTIC_SIMULATION_INTENTS.get(intent_id)
    if not mapping:
        return None
    updates, label = mapping
    return ArchitectureSimulationSpec(
        scenario_id=intent_id.replace(":", "_"),
        label=label,
        slot_updates=updates,
        user_message_excerpt="",
    )


def detect_architecture_simulation(
    message: str,
    intent_result: IntentResult | None = None,
) -> ArchitectureSimulationSpec | None:
    """Match conversational scenarios — regex first, then semantic intent."""
    spec = _detect_architecture_simulation_regex(message)
    if spec:
        spec.user_message_excerpt = message[:200]
        return spec
    semantic = simulation_from_intent(intent_result)
    if semantic:
        semantic.user_message_excerpt = message[:200]
        logger.info("architecture simulation via semantic intent=%s", intent_result.intent_id)
        return semantic
    return None


def _detect_architecture_simulation_regex(message: str) -> ArchitectureSimulationSpec | None:
    """Regex-based scenario detection (fast path)."""
    lower = message.lower().strip()
    if not lower:
        return None
    if "what if" not in lower and "what would change" not in lower and "simulate" not in lower:
        if not any(
            p in lower
            for p in (
                "if traffic",
                "if latency",
                "if we move to self",
                "if scale",
                "if budget",
                "if privacy",
            )
        ):
            return None

    for idx, (pattern, updates, label) in enumerate(_SIMULATION_PATTERNS):
        if re.search(pattern, lower):
            return ArchitectureSimulationSpec(
                scenario_id=f"scenario_{idx}",
                label=label,
                slot_updates=updates,
                user_message_excerpt="",
            )
    return None


def apply_simulation_to_state(
    state: ConstraintState,
    spec: ArchitectureSimulationSpec,
) -> ConstraintState:
    """Return new ConstraintState with simulation slots applied."""
    trial = state.model_copy(deep=True)
    for key, value in spec.slot_updates.items():
        trial.set_slot(
            key,
            value,
            source=ConstraintSource.EXPLICIT,
            confidence=1.0,
            force=True,
        )
    return trial


def build_simulation_narrative(
    spec: ArchitectureSimulationSpec,
    replacements: list[dict[str, str]],
) -> str:
    parts = [f"Simulating: **{spec.label}**."]
    if replacements:
        changes = ", ".join(
            f"{r['from_label']} → {r['to_label']}" for r in replacements[:3]
        )
        parts.append(f" Components affected: {changes}.")
    else:
        parts.append(" Stack remains stable under this scenario — tradeoffs shift in emphasis.")
    return " ".join(parts)
