"""Intentions de decision du cerveau."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class DecisionKind(StrEnum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"


@dataclass(frozen=True)
class DecisionIntent:
    kind: DecisionKind
    amount: int | None = None
    confidence: float | None = None
    reasoning: str | None = None

    @property
    def ui_label(self) -> str:
        if self.kind is DecisionKind.ALL_IN:
            return "All-In"
        return self.kind.value.title()

    @property
    def requires_amount(self) -> bool:
        return self.kind in {DecisionKind.BET, DecisionKind.RAISE}

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "ui_label": self.ui_label,
            "amount": self.amount,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }
