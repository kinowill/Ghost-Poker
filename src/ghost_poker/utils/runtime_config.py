"""Configuration runtime explicite pour Ghost-Poker."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from dotenv import load_dotenv


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _default_control_state_path() -> Path:
    return _project_root() / "data" / "runtime" / "control_panel_state.json"


class ControlMode(StrEnum):
    ASSIST = "assist"
    AUTONOMOUS = "autonomous"


class ExecutionSafety(StrEnum):
    DRY_RUN = "dry_run"
    ARMED = "armed"


class ControlGateMode(StrEnum):
    DISABLED = "disabled"
    PANEL = "panel"


class MetaBackendKind(StrEnum):
    DISABLED = "disabled"
    MISTRAL = "mistral"
    GROQ = "groq"
    OPENAI_COMPATIBLE = "openai_compatible"
    OLLAMA = "ollama"
    LOCAL = "local"


@dataclass(frozen=True)
class MetaBackendConfig:
    kind: MetaBackendKind = MetaBackendKind.DISABLED
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None

    @property
    def is_enabled(self) -> bool:
        return self.kind is not MetaBackendKind.DISABLED

    @property
    def is_remote(self) -> bool:
        return self.kind in {
            MetaBackendKind.MISTRAL,
            MetaBackendKind.GROQ,
            MetaBackendKind.OPENAI_COMPATIBLE,
        }


@dataclass(frozen=True)
class RuntimeConfig:
    control_mode: ControlMode = ControlMode.ASSIST
    execution_safety: ExecutionSafety = ExecutionSafety.DRY_RUN
    control_gate_mode: ControlGateMode = ControlGateMode.DISABLED
    control_state_path: Path = field(default_factory=_default_control_state_path)
    log_level: str = "INFO"
    kill_switch_key: str = "f12"
    meta_backend: MetaBackendConfig = field(default_factory=MetaBackendConfig)


def _parse_enum(raw_value: str | None, enum_cls: type[StrEnum], default: StrEnum) -> StrEnum:
    if raw_value is None or not raw_value.strip():
        return default

    normalized = raw_value.strip().lower().replace("-", "_")
    for item in enum_cls:
        if item.value == normalized:
            return item

    allowed = ", ".join(item.value for item in enum_cls)
    raise ValueError(f"Valeur invalide '{raw_value}' pour {enum_cls.__name__}. Valeurs: {allowed}.")


def _resolve_meta_api_key(env: Mapping[str, str], kind: MetaBackendKind) -> str | None:
    generic_key = env.get("GHOST_POKER_META_API_KEY")
    if generic_key:
        return generic_key

    if kind is MetaBackendKind.MISTRAL:
        return env.get("MISTRAL_API_KEY")
    if kind is MetaBackendKind.GROQ:
        return env.get("GROQ_API_KEY")
    return None


def _build_meta_backend(env: Mapping[str, str]) -> MetaBackendConfig:
    kind = _parse_enum(
        env.get("GHOST_POKER_META_BACKEND"),
        MetaBackendKind,
        MetaBackendKind.DISABLED,
    )
    assert isinstance(kind, MetaBackendKind)
    return MetaBackendConfig(
        kind=kind,
        model=env.get("GHOST_POKER_META_MODEL") or None,
        api_key=_resolve_meta_api_key(env, kind),
        base_url=env.get("GHOST_POKER_META_BASE_URL") or None,
    )


def _resolve_control_state_path(env: Mapping[str, str]) -> Path:
    raw_path = env.get("GHOST_POKER_CONTROL_STATE_PATH")
    if raw_path and raw_path.strip():
        return Path(raw_path).expanduser()
    return _default_control_state_path()


def load_runtime_config(
    env: Mapping[str, str] | None = None,
    *,
    load_project_dotenv: bool = True,
) -> RuntimeConfig:
    """Charge la config runtime depuis l'environnement."""
    if env is None:
        if load_project_dotenv:
            load_dotenv(_project_root() / ".env", override=False)
        env = os.environ

    control_mode = _parse_enum(
        env.get("GHOST_POKER_CONTROL_MODE"),
        ControlMode,
        ControlMode.ASSIST,
    )
    assert isinstance(control_mode, ControlMode)
    execution_safety = _parse_enum(
        env.get("GHOST_POKER_EXECUTION_SAFETY"),
        ExecutionSafety,
        ExecutionSafety.DRY_RUN,
    )
    assert isinstance(execution_safety, ExecutionSafety)
    control_gate_mode = _parse_enum(
        env.get("GHOST_POKER_CONTROL_GATE_MODE"),
        ControlGateMode,
        ControlGateMode.DISABLED,
    )
    assert isinstance(control_gate_mode, ControlGateMode)

    return RuntimeConfig(
        control_mode=control_mode,
        execution_safety=execution_safety,
        control_gate_mode=control_gate_mode,
        control_state_path=_resolve_control_state_path(env),
        log_level=env.get("GHOST_POKER_LOG_LEVEL", "INFO"),
        kill_switch_key=env.get("GHOST_POKER_KILL_SWITCH_KEY", "f12"),
        meta_backend=_build_meta_backend(env),
    )
