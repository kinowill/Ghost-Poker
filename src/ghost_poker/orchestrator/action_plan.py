"""Contrat d'action entre cerveau, orchestrateur et controle."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ghost_poker.brain import DecisionIntent, DecisionKind
from ghost_poker.orchestrator.runtime_profile import RuntimeProfile
from ghost_poker.perception.table_state import ActionOption, TableState


@dataclass(frozen=True)
class ResolvedActionTarget:
    label: str
    hotkey: str | None = None
    amount: int | None = None
    uses_slider: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "hotkey": self.hotkey,
            "amount": self.amount,
            "uses_slider": self.uses_slider,
        }


@dataclass(frozen=True)
class ActionPlan:
    decision: DecisionIntent
    control_mode: str
    should_execute: bool
    requires_manual_confirmation: bool
    target: ResolvedActionTarget | None = None
    available_actions: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blocking_issues: list[str] = field(default_factory=list)

    @property
    def is_actionable(self) -> bool:
        return self.target is not None and not self.blocking_issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.to_dict(),
            "control_mode": self.control_mode,
            "should_execute": self.should_execute,
            "requires_manual_confirmation": self.requires_manual_confirmation,
            "target": self.target.to_dict() if self.target else None,
            "available_actions": self.available_actions,
            "warnings": self.warnings,
            "blocking_issues": self.blocking_issues,
            "is_actionable": self.is_actionable,
        }


def _available_actions_payload(table_state: TableState) -> list[dict[str, Any]]:
    payload = [option.to_dict() for option in table_state.actions.options]
    if table_state.actions.all_in_hotkey:
        payload.append(
            {
                "label": "All-In",
                "hotkey": table_state.actions.all_in_hotkey,
                "amount": None,
            }
        )
    return payload


def _resolve_standard_action(
    table_state: TableState,
    decision: DecisionIntent,
    warnings: list[str],
    blocking_issues: list[str],
) -> ResolvedActionTarget | None:
    target_option: ActionOption | None = None
    for option in table_state.actions.options:
        if option.label.strip().lower() == decision.kind.value:
            target_option = option
            break

    if target_option is None:
        blocking_issues.append(f"action '{decision.ui_label}' indisponible dans l'etat courant")
        return None

    resolved_amount = target_option.amount
    uses_slider = False

    if decision.requires_amount and decision.amount is not None:
        if target_option.amount is None:
            if table_state.actions.slider_amount is None:
                blocking_issues.append(
                    f"aucun montant visible pour '{decision.ui_label}' et slider introuvable"
                )
                return None
            resolved_amount = decision.amount
            uses_slider = True
        elif target_option.amount != decision.amount:
            if table_state.actions.slider_amount is None:
                blocking_issues.append(
                    f"montant desire {decision.amount} different du bouton {target_option.amount}"
                )
                return None
            resolved_amount = decision.amount
            uses_slider = True
            warnings.append(
                f"montant {decision.amount} necessite un override slider au lieu du bouton {target_option.amount}"
            )

    return ResolvedActionTarget(
        label=target_option.label,
        hotkey=target_option.hotkey,
        amount=resolved_amount,
        uses_slider=uses_slider,
    )


def _resolve_all_in_action(
    table_state: TableState,
    blocking_issues: list[str],
) -> ResolvedActionTarget | None:
    if not table_state.actions.all_in_hotkey:
        blocking_issues.append("action 'All-In' indisponible dans l'etat courant")
        return None

    return ResolvedActionTarget(
        label="All-In",
        hotkey=table_state.actions.all_in_hotkey,
    )


def build_action_plan(
    runtime_profile: RuntimeProfile,
    table_state: TableState,
    decision: DecisionIntent,
) -> ActionPlan:
    warnings = list(runtime_profile.warnings)
    blocking_issues: list[str] = []

    if decision.kind is DecisionKind.ALL_IN:
        target = _resolve_all_in_action(table_state, blocking_issues)
    else:
        target = _resolve_standard_action(table_state, decision, warnings, blocking_issues)

    return ActionPlan(
        decision=decision,
        control_mode=runtime_profile.runtime_config.control_mode.value,
        should_execute=runtime_profile.control_policy.executes_actions,
        requires_manual_confirmation=runtime_profile.control_policy.requires_manual_confirmation,
        target=target,
        available_actions=_available_actions_payload(table_state),
        warnings=warnings,
        blocking_issues=blocking_issues,
    )
