"""Politique d'execution selon le mode runtime."""

from __future__ import annotations

from dataclasses import dataclass

from ghost_poker.utils.runtime_config import ControlMode


@dataclass(frozen=True)
class ControlPolicy:
    mode: ControlMode
    executes_actions: bool
    exposes_recommendations: bool
    requires_manual_confirmation: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode.value,
            "executes_actions": self.executes_actions,
            "exposes_recommendations": self.exposes_recommendations,
            "requires_manual_confirmation": self.requires_manual_confirmation,
        }


def build_control_policy(mode: ControlMode) -> ControlPolicy:
    if mode is ControlMode.AUTONOMOUS:
        return ControlPolicy(
            mode=mode,
            executes_actions=True,
            exposes_recommendations=True,
            requires_manual_confirmation=False,
        )

    return ControlPolicy(
        mode=mode,
        executes_actions=False,
        exposes_recommendations=True,
        requires_manual_confirmation=True,
    )
