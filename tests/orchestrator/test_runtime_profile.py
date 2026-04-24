from ghost_poker.orchestrator import build_runtime_profile
from ghost_poker.utils import load_runtime_config


def test_runtime_profile_warns_when_autonomous_mode_is_active() -> None:
    runtime_config = load_runtime_config(
        {
            "GHOST_POKER_CONTROL_MODE": "autonomous",
            "GHOST_POKER_EXECUTION_SAFETY": "dry_run",
            "GHOST_POKER_META_BACKEND": "disabled",
        },
        load_project_dotenv=False,
    )

    profile = build_runtime_profile(runtime_config)

    assert profile.is_autonomous is True
    assert any("mode autonomous actif" in warning for warning in profile.warnings)
    assert any("dry_run" in warning for warning in profile.warnings)


def test_runtime_profile_exposes_meta_backend_summary() -> None:
    runtime_config = load_runtime_config(
        {
            "GHOST_POKER_META_BACKEND": "local",
            "GHOST_POKER_META_MODEL": "llama-poker.gguf",
        },
        load_project_dotenv=False,
    )

    profile = build_runtime_profile(runtime_config)
    payload = profile.to_dict()

    assert payload["control_mode"] == "assist"
    assert payload["control_gate_mode"] == "disabled"
    assert payload["meta_backend"]["kind"] == "local"
    assert payload["meta_backend"]["model"] == "llama-poker.gguf"
    assert payload["meta_backend"]["has_api_key"] is False


def test_runtime_profile_warns_when_visible_control_panel_is_active() -> None:
    runtime_config = load_runtime_config(
        {
            "GHOST_POKER_CONTROL_MODE": "autonomous",
            "GHOST_POKER_EXECUTION_SAFETY": "armed",
            "GHOST_POKER_CONTROL_GATE_MODE": "panel",
        },
        load_project_dotenv=False,
    )

    profile = build_runtime_profile(runtime_config)

    assert any("control panel actif" in warning for warning in profile.warnings)
