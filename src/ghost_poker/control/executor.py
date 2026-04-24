"""Execution OS gardee d'un ActionPlan."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import pyautogui

from ghost_poker.control.kill_switch import is_kill_switch_pressed
from ghost_poker.control.panel_state import (
    ControlPanelStatus,
    load_control_panel_state,
    set_control_panel_state,
)
from ghost_poker.orchestrator.action_plan import ActionPlan
from ghost_poker.utils import ControlGateMode, ExecutionSafety

pyautogui.FAILSAFE = True


class ExecutionStatus(StrEnum):
    SKIPPED = "skipped"
    DRY_RUN = "dry_run"
    BLOCKED = "blocked"
    EXECUTED = "executed"


@dataclass(frozen=True)
class ExecutionResult:
    status: ExecutionStatus
    reason: str
    hotkey_sent: str | None = None
    debug: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "status": self.status.value,
            "reason": self.reason,
            "hotkey_sent": self.hotkey_sent,
        }
        if self.debug is not None:
            payload["debug"] = self.debug
        return payload


def _read_control_panel_debug(
    control_gate_mode: ControlGateMode,
    control_state_path: Path | None,
) -> dict[str, object] | None:
    if control_gate_mode is not ControlGateMode.PANEL or control_state_path is None:
        return None

    state = load_control_panel_state(control_state_path)
    return {
        "path": str(control_state_path),
        **state.to_dict(),
    }


def _block_with_control_panel(
    control_gate_mode: ControlGateMode,
    control_state_path: Path | None,
) -> ExecutionResult | None:
    debug = _read_control_panel_debug(control_gate_mode, control_state_path)
    if debug is None or bool(debug["allows_execution"]):
        return None
    return ExecutionResult(
        status=ExecutionStatus.BLOCKED,
        reason=f"control panel '{debug['status']}'",
        debug={"control_panel": debug},
    )


def _maybe_consume_control_panel_arm(
    control_gate_mode: ControlGateMode,
    control_state_path: Path | None,
) -> dict[str, object] | None:
    debug = _read_control_panel_debug(control_gate_mode, control_state_path)
    if debug is None:
        return None
    if not bool(debug["consume_after_execution"]) or control_state_path is None:
        return {"control_panel": debug}

    consumed = set_control_panel_state(
        control_state_path,
        ControlPanelStatus.PAUSED,
        note="armed_once consumed after execution",
    )
    return {
        "control_panel_before_execute": debug,
        "control_panel_after_execute": {
            "path": str(control_state_path),
            **consumed.to_dict(),
        },
    }


def observe_armed_window(
    *,
    armed_delay_ms: int,
    kill_switch_key: str,
    arm_key: str | None = None,
    control_gate_mode: ControlGateMode = ControlGateMode.DISABLED,
    control_state_path: Path | None = None,
) -> dict[str, Any]:
    delay_seconds = armed_delay_ms / 1000
    started_at = time.monotonic()
    arm_seen = arm_key is None
    arm_seen_samples = 0
    kill_switch_seen = False
    control_panel: dict[str, object] | None = None
    sample_count = 0

    while (time.monotonic() - started_at) < delay_seconds:
        sample_count += 1
        control_panel = _read_control_panel_debug(control_gate_mode, control_state_path)
        if control_panel is not None and not bool(control_panel["allows_execution"]):
            break
        if is_kill_switch_pressed(kill_switch_key):
            kill_switch_seen = True
            break
        if arm_key and is_kill_switch_pressed(arm_key):
            arm_seen = True
            arm_seen_samples += 1
        time.sleep(0.05)

    payload = {
        "armed_delay_ms": armed_delay_ms,
        "arm_key": arm_key,
        "arm_seen": arm_seen,
        "arm_seen_samples": arm_seen_samples,
        "kill_switch_key": kill_switch_key,
        "kill_switch_seen": kill_switch_seen,
        "sample_count": sample_count,
    }
    if control_panel is not None:
        payload["control_panel"] = control_panel
    return payload


def execute_action_plan(
    action_plan: ActionPlan,
    *,
    execution_safety: ExecutionSafety,
    kill_switch_key: str,
    armed_delay_ms: int = 0,
    arm_key: str | None = None,
    control_gate_mode: ControlGateMode = ControlGateMode.DISABLED,
    control_state_path: Path | None = None,
) -> ExecutionResult:
    if not action_plan.should_execute:
        return ExecutionResult(
            status=ExecutionStatus.SKIPPED,
            reason="mode runtime non executable",
        )

    if not action_plan.is_actionable or action_plan.target is None:
        return ExecutionResult(
            status=ExecutionStatus.BLOCKED,
            reason="action plan non actionnable",
        )

    if action_plan.target.uses_slider:
        return ExecutionResult(
            status=ExecutionStatus.BLOCKED,
            reason="execution slider non implementee a ce stade",
        )

    if not action_plan.target.hotkey:
        return ExecutionResult(
            status=ExecutionStatus.BLOCKED,
            reason="aucune hotkey disponible pour l'action cible",
        )

    control_panel_block = _block_with_control_panel(control_gate_mode, control_state_path)
    if control_panel_block is not None:
        return control_panel_block

    if is_kill_switch_pressed(kill_switch_key):
        return ExecutionResult(
            status=ExecutionStatus.BLOCKED,
            reason=f"kill switch '{kill_switch_key}' detecte",
        )

    if execution_safety is ExecutionSafety.DRY_RUN:
        return ExecutionResult(
            status=ExecutionStatus.DRY_RUN,
            reason="execution simulee (dry_run)",
            hotkey_sent=action_plan.target.hotkey,
        )

    if armed_delay_ms > 0:
        debug = observe_armed_window(
            armed_delay_ms=armed_delay_ms,
            kill_switch_key=kill_switch_key,
            arm_key=arm_key,
            control_gate_mode=control_gate_mode,
            control_state_path=control_state_path,
        )
        control_panel = debug.get("control_panel")
        if control_panel is not None and not bool(control_panel["allows_execution"]):
            return ExecutionResult(
                status=ExecutionStatus.BLOCKED,
                reason=f"control panel '{control_panel['status']}' pendant le delai arme",
                debug=debug,
            )
        if debug["kill_switch_seen"]:
            return ExecutionResult(
                status=ExecutionStatus.BLOCKED,
                reason=f"kill switch '{kill_switch_key}' detecte pendant le delai arme",
                debug=debug,
            )
        if arm_key and not debug["arm_seen"]:
            return ExecutionResult(
                status=ExecutionStatus.BLOCKED,
                reason=f"arm key '{arm_key}' non detectee pendant le delai arme",
                debug=debug,
            )
    else:
        debug = None

    pyautogui.press(action_plan.target.hotkey.lower())
    control_panel_debug = _maybe_consume_control_panel_arm(control_gate_mode, control_state_path)
    if debug is None:
        debug = control_panel_debug
    elif control_panel_debug:
        debug = {**debug, **control_panel_debug}
    return ExecutionResult(
        status=ExecutionStatus.EXECUTED,
        reason="hotkey envoyee",
        hotkey_sent=action_plan.target.hotkey,
        debug=debug,
    )
