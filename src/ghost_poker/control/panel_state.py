"""Etat partage du panneau de controle visible."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path


class ControlPanelStatus(StrEnum):
    STOPPED = "stopped"
    PAUSED = "paused"
    ARMED = "armed"
    ARMED_ONCE = "armed_once"


@dataclass(frozen=True)
class ControlPanelState:
    status: ControlPanelStatus = ControlPanelStatus.PAUSED
    note: str = ""
    updated_at: str | None = None

    @property
    def allows_execution(self) -> bool:
        return self.status in {ControlPanelStatus.ARMED, ControlPanelStatus.ARMED_ONCE}

    @property
    def consume_after_execution(self) -> bool:
        return self.status is ControlPanelStatus.ARMED_ONCE

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "note": self.note,
            "updated_at": self.updated_at,
            "allows_execution": self.allows_execution,
            "consume_after_execution": self.consume_after_execution,
        }


def _timestamp_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def default_control_panel_state(*, note: str = "default paused state") -> ControlPanelState:
    return ControlPanelState(
        status=ControlPanelStatus.PAUSED,
        note=note,
        updated_at=_timestamp_now(),
    )


def _normalize_status(raw_status: str | None) -> ControlPanelStatus | None:
    if raw_status is None:
        return None
    normalized = raw_status.strip().lower().replace("-", "_")
    for status in ControlPanelStatus:
        if status.value == normalized:
            return status
    return None


def load_control_panel_state(path: Path) -> ControlPanelState:
    if not path.exists():
        return default_control_panel_state(note="state file absent")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_control_panel_state(note="invalid state file")

    status = _normalize_status(payload.get("status"))
    if status is None:
        return default_control_panel_state(note="invalid state status")

    return ControlPanelState(
        status=status,
        note=str(payload.get("note") or ""),
        updated_at=payload.get("updated_at") or None,
    )


def save_control_panel_state(path: Path, state: ControlPanelState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def set_control_panel_state(
    path: Path,
    status: ControlPanelStatus,
    *,
    note: str = "",
) -> ControlPanelState:
    state = ControlPanelState(status=status, note=note, updated_at=_timestamp_now())
    save_control_panel_state(path, state)
    return state
