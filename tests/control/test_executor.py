from pathlib import Path
import shutil
from unittest.mock import patch
from uuid import uuid4

from ghost_poker.control.executor import ExecutionStatus, execute_action_plan, observe_armed_window
from ghost_poker.control.panel_state import ControlPanelStatus, set_control_panel_state
from ghost_poker.orchestrator import ActionPlan, ResolvedActionTarget
from ghost_poker.utils import ControlGateMode, ExecutionSafety
from ghost_poker.brain import DecisionIntent, DecisionKind


def _sample_action_plan(*, should_execute: bool = True, uses_slider: bool = False) -> ActionPlan:
    return ActionPlan(
        decision=DecisionIntent(kind=DecisionKind.CALL, amount=20),
        control_mode="autonomous",
        should_execute=should_execute,
        requires_manual_confirmation=False,
        target=ResolvedActionTarget(
            label="Call",
            hotkey="F2",
            amount=20,
            uses_slider=uses_slider,
        ),
        available_actions=[],
        warnings=[],
        blocking_issues=[],
    )


def _make_workspace_tmp_dir() -> Path:
    path = Path("data/test_tmp") / f"executor-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_execute_action_plan_skips_non_executable_mode() -> None:
    result = execute_action_plan(
        _sample_action_plan(should_execute=False),
        execution_safety=ExecutionSafety.ARMED,
        kill_switch_key="f12",
    )

    assert result.status is ExecutionStatus.SKIPPED


def test_execute_action_plan_stays_in_dry_run_by_default() -> None:
    with patch("ghost_poker.control.executor.is_kill_switch_pressed", return_value=False):
        result = execute_action_plan(
            _sample_action_plan(),
            execution_safety=ExecutionSafety.DRY_RUN,
            kill_switch_key="f12",
        )

    assert result.status is ExecutionStatus.DRY_RUN
    assert result.hotkey_sent == "F2"


def test_execute_action_plan_blocks_when_kill_switch_is_pressed() -> None:
    with patch("ghost_poker.control.executor.is_kill_switch_pressed", return_value=True):
        result = execute_action_plan(
            _sample_action_plan(),
            execution_safety=ExecutionSafety.ARMED,
            kill_switch_key="f12",
        )

    assert result.status is ExecutionStatus.BLOCKED
    assert "kill switch" in result.reason


def test_execute_action_plan_executes_hotkey_in_armed_mode() -> None:
    with (
        patch("ghost_poker.control.executor.is_kill_switch_pressed", return_value=False),
        patch("ghost_poker.control.executor.pyautogui.press") as press_mock,
    ):
        result = execute_action_plan(
            _sample_action_plan(),
            execution_safety=ExecutionSafety.ARMED,
            kill_switch_key="f12",
        )

    press_mock.assert_called_once_with("f2")
    assert result.status is ExecutionStatus.EXECUTED


def test_execute_action_plan_blocks_slider_actions_for_now() -> None:
    with patch("ghost_poker.control.executor.is_kill_switch_pressed", return_value=False):
        result = execute_action_plan(
            _sample_action_plan(uses_slider=True),
            execution_safety=ExecutionSafety.ARMED,
            kill_switch_key="f12",
        )

    assert result.status is ExecutionStatus.BLOCKED
    assert "slider" in result.reason


def test_execute_action_plan_checks_kill_switch_again_after_delay() -> None:
    with (
        patch(
            "ghost_poker.control.executor.is_kill_switch_pressed",
            side_effect=[False, True],
        ),
        patch("ghost_poker.control.executor.time.sleep") as sleep_mock,
    ):
        result = execute_action_plan(
            _sample_action_plan(),
            execution_safety=ExecutionSafety.ARMED,
            kill_switch_key="f12",
            armed_delay_ms=1500,
        )

    sleep_mock.assert_not_called()
    assert result.status is ExecutionStatus.BLOCKED
    assert "pendant le delai arme" in result.reason


def test_execute_action_plan_blocks_if_arm_key_is_never_seen() -> None:
    def fake_key_state(key_name: str) -> bool:
        return False

    with (
        patch("ghost_poker.control.executor.is_kill_switch_pressed", side_effect=fake_key_state),
        patch("ghost_poker.control.executor.time.monotonic", side_effect=[0.0, 0.1, 0.2, 0.31]),
        patch("ghost_poker.control.executor.time.sleep"),
    ):
        result = execute_action_plan(
            _sample_action_plan(),
            execution_safety=ExecutionSafety.ARMED,
            kill_switch_key="f12",
            armed_delay_ms=300,
            arm_key="f10",
        )

    assert result.status is ExecutionStatus.BLOCKED
    assert "arm key 'f10'" in result.reason
    assert result.debug is not None
    assert result.debug["armed_delay_ms"] == 300
    assert result.debug["arm_key"] == "f10"
    assert result.debug["arm_seen"] is False
    assert result.debug["arm_seen_samples"] == 0
    assert result.debug["sample_count"] >= 2


def test_execute_action_plan_executes_when_arm_key_is_seen_during_delay() -> None:
    seen = {"arm": False}

    def fake_key_state(key_name: str) -> bool:
        if key_name == "f12":
            return False
        if key_name == "f10" and not seen["arm"]:
            seen["arm"] = True
            return True
        return False

    with (
        patch("ghost_poker.control.executor.is_kill_switch_pressed", side_effect=fake_key_state),
        patch("ghost_poker.control.executor.time.monotonic", side_effect=[0.0, 0.1, 0.2, 0.31]),
        patch("ghost_poker.control.executor.time.sleep"),
        patch("ghost_poker.control.executor.pyautogui.press") as press_mock,
    ):
        result = execute_action_plan(
            _sample_action_plan(),
            execution_safety=ExecutionSafety.ARMED,
            kill_switch_key="f12",
            armed_delay_ms=300,
            arm_key="f10",
        )

    press_mock.assert_called_once_with("f2")
    assert result.status is ExecutionStatus.EXECUTED
    assert result.debug is not None
    assert result.debug["armed_delay_ms"] == 300
    assert result.debug["arm_key"] == "f10"
    assert result.debug["arm_seen"] is True
    assert result.debug["arm_seen_samples"] >= 1
    assert result.debug["sample_count"] >= 2


def test_observe_armed_window_reports_arm_and_kill_switch_state() -> None:
    seen = {"arm": False}

    def fake_key_state(key_name: str) -> bool:
        if key_name == "f12":
            return False
        if key_name == "f10" and not seen["arm"]:
            seen["arm"] = True
            return True
        return False

    with (
        patch("ghost_poker.control.executor.is_kill_switch_pressed", side_effect=fake_key_state),
        patch("ghost_poker.control.executor.time.monotonic", side_effect=[0.0, 0.1, 0.2, 0.31]),
        patch("ghost_poker.control.executor.time.sleep"),
    ):
        debug = observe_armed_window(
            armed_delay_ms=300,
            kill_switch_key="f12",
            arm_key="f10",
        )

    assert debug["armed_delay_ms"] == 300
    assert debug["arm_key"] == "f10"
    assert debug["kill_switch_key"] == "f12"
    assert debug["arm_seen"] is True
    assert debug["arm_seen_samples"] >= 1
    assert debug["kill_switch_seen"] is False
    assert debug["sample_count"] >= 2


def test_execute_action_plan_blocks_when_control_panel_is_paused() -> None:
    tmp_dir = _make_workspace_tmp_dir()
    try:
        state_path = tmp_dir / "control_panel_state.json"
        set_control_panel_state(state_path, ControlPanelStatus.PAUSED, note="paused in test")
        with patch("ghost_poker.control.executor.is_kill_switch_pressed", return_value=False):
            result = execute_action_plan(
                _sample_action_plan(),
                execution_safety=ExecutionSafety.ARMED,
                kill_switch_key="f12",
                control_gate_mode=ControlGateMode.PANEL,
                control_state_path=state_path,
            )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    assert result.status is ExecutionStatus.BLOCKED
    assert result.reason == "control panel 'paused'"
    assert result.debug is not None
    assert result.debug["control_panel"]["status"] == "paused"


def test_execute_action_plan_consumes_one_shot_control_panel_arm() -> None:
    tmp_dir = _make_workspace_tmp_dir()
    try:
        state_path = tmp_dir / "control_panel_state.json"
        set_control_panel_state(state_path, ControlPanelStatus.ARMED_ONCE, note="one shot")
        with (
            patch("ghost_poker.control.executor.is_kill_switch_pressed", return_value=False),
            patch("ghost_poker.control.executor.pyautogui.press") as press_mock,
        ):
            result = execute_action_plan(
                _sample_action_plan(),
                execution_safety=ExecutionSafety.ARMED,
                kill_switch_key="f12",
                control_gate_mode=ControlGateMode.PANEL,
                control_state_path=state_path,
            )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    press_mock.assert_called_once_with("f2")
    assert result.status is ExecutionStatus.EXECUTED
    assert result.debug is not None
    assert result.debug["control_panel_after_execute"]["status"] == "paused"
