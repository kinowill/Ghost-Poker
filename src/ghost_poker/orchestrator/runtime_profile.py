"""Profil runtime derive de la configuration projet."""

from __future__ import annotations

from dataclasses import dataclass, field

from ghost_poker.brain.meta_backend import (
    MetaBackendSpec,
    get_meta_backend_spec,
    validate_meta_backend_config,
)
from ghost_poker.control.runtime_mode import ControlPolicy, build_control_policy
from ghost_poker.utils import ControlGateMode, RuntimeConfig


@dataclass(frozen=True)
class RuntimeProfile:
    runtime_config: RuntimeConfig
    control_policy: ControlPolicy
    meta_backend_spec: MetaBackendSpec
    warnings: list[str] = field(default_factory=list)

    @property
    def is_autonomous(self) -> bool:
        return self.control_policy.executes_actions

    def to_dict(self) -> dict[str, object]:
        return {
            "control_mode": self.runtime_config.control_mode.value,
            "execution_safety": self.runtime_config.execution_safety.value,
            "control_gate_mode": self.runtime_config.control_gate_mode.value,
            "control_state_path": str(self.runtime_config.control_state_path),
            "log_level": self.runtime_config.log_level,
            "kill_switch_key": self.runtime_config.kill_switch_key,
            "control_policy": self.control_policy.to_dict(),
            "meta_backend": {
                **self.meta_backend_spec.to_dict(),
                "model": self.runtime_config.meta_backend.model,
                "base_url": self.runtime_config.meta_backend.base_url,
                "has_api_key": bool(self.runtime_config.meta_backend.api_key),
            },
            "warnings": self.warnings,
        }


def build_runtime_profile(runtime_config: RuntimeConfig) -> RuntimeProfile:
    control_policy = build_control_policy(runtime_config.control_mode)
    meta_backend_spec = get_meta_backend_spec(runtime_config.meta_backend.kind)
    warnings = validate_meta_backend_config(runtime_config.meta_backend)

    if control_policy.executes_actions:
        warnings.append(
            "mode autonomous actif : toute integration future devra verifier kill switch "
            "et garde-fous"
        )
        if runtime_config.execution_safety.value == "dry_run":
            warnings.append("mode autonomous en dry_run : aucune action OS reelle ne sera executee")
        elif runtime_config.control_gate_mode is ControlGateMode.PANEL:
            warnings.append("control panel actif : l'execution depend du panneau visible local")

    if not runtime_config.kill_switch_key.strip():
        warnings.append("aucune touche kill switch configuree")

    return RuntimeProfile(
        runtime_config=runtime_config,
        control_policy=control_policy,
        meta_backend_spec=meta_backend_spec,
        warnings=warnings,
    )
