"""Canonical constraint memory for Phase-2 deterministic advisor reasoning."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ConstraintSource(str, Enum):
    EXPLICIT = "explicit"
    INFERRED = "inferred"
    OPTION_CARD = "option_card"
    ACCUMULATED = "accumulated"
    DEFAULT = "default"


class ConstraintSlot(BaseModel):
    """One decision slot with provenance."""

    value: str | int | float | bool | list[str] = Field(description="Normalized slot value")
    source: ConstraintSource = ConstraintSource.INFERRED
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    raw_label: str | None = Field(default=None, description="Original UI label if from option card")


class ConstraintState(BaseModel):
    """Structured constraint memory — single source of truth for a conversation turn."""

    slots: dict[str, ConstraintSlot] = Field(default_factory=dict)
    playbook_id: str | None = None
    version: str = "1"

    def get(self, key: str, default: Any = None) -> Any:
        slot = self.slots.get(key)
        return slot.value if slot is not None else default

    def has(self, key: str) -> bool:
        return key in self.slots

    def set_slot(
        self,
        key: str,
        value: Any,
        *,
        source: ConstraintSource,
        confidence: float,
        raw_label: str | None = None,
        force: bool = False,
    ) -> None:
        """Merge with precedence: explicit/option_card beats inferred unless force."""
        incoming = ConstraintSlot(
            value=value,
            source=source,
            confidence=confidence,
            raw_label=raw_label,
        )
        existing = self.slots.get(key)
        if existing is None or force or _source_rank(incoming.source) >= _source_rank(existing.source):
            self.slots[key] = incoming

    def slot_values(self) -> dict[str, Any]:
        """Flat slot values for trace snapshots and logging (read-only export)."""
        return {key: slot.value for key, slot in self.slots.items()}

    def merge_flat_slot_values(
        self,
        values: dict[str, Any],
        *,
        source: ConstraintSource,
    ) -> None:
        """Import flat key→value maps from option-card metadata only."""
        for key, value in values.items():
            if value is None:
                continue
            self.set_slot(
                key,
                value,
                source=source,
                confidence=0.9 if source == ConstraintSource.OPTION_CARD else 0.75,
            )


def _source_rank(source: ConstraintSource) -> int:
    order = {
        ConstraintSource.DEFAULT: 0,
        ConstraintSource.INFERRED: 1,
        ConstraintSource.ACCUMULATED: 2,
        ConstraintSource.OPTION_CARD: 3,
        ConstraintSource.EXPLICIT: 4,
    }
    return order.get(source, 0)
