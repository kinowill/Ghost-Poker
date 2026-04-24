from pathlib import Path
import shutil
from uuid import uuid4

from ghost_poker.control.panel_state import (
    ControlPanelStatus,
    default_control_panel_state,
    load_control_panel_state,
    set_control_panel_state,
)


def _make_workspace_tmp_dir() -> Path:
    path = Path("data/test_tmp") / f"panel_state-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_load_control_panel_state_defaults_to_paused_when_file_is_missing() -> None:
    tmp_dir = _make_workspace_tmp_dir()
    try:
        state = load_control_panel_state(tmp_dir / "missing.json")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    assert state.status is ControlPanelStatus.PAUSED
    assert state.allows_execution is False


def test_set_control_panel_state_persists_visible_status() -> None:
    tmp_dir = _make_workspace_tmp_dir()
    try:
        path = tmp_dir / "control_panel_state.json"
        written = set_control_panel_state(path, ControlPanelStatus.ARMED_ONCE, note="test arm once")
        loaded = load_control_panel_state(path)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    assert written.status is ControlPanelStatus.ARMED_ONCE
    assert loaded.status is ControlPanelStatus.ARMED_ONCE
    assert loaded.allows_execution is True
    assert loaded.consume_after_execution is True
    assert loaded.note == "test arm once"


def test_default_control_panel_state_is_paused() -> None:
    state = default_control_panel_state()

    assert state.status is ControlPanelStatus.PAUSED
    assert state.allows_execution is False
