from ghost_poker.utils.runtime_config import (
    ControlGateMode,
    ControlMode,
    ExecutionSafety,
    MetaBackendKind,
    load_runtime_config,
)


def test_load_runtime_config_defaults_to_assist_and_disabled_meta() -> None:
    config = load_runtime_config({}, load_project_dotenv=False)

    assert config.control_mode is ControlMode.ASSIST
    assert config.execution_safety is ExecutionSafety.DRY_RUN
    assert config.control_gate_mode is ControlGateMode.DISABLED
    assert config.meta_backend.kind is MetaBackendKind.DISABLED
    assert config.meta_backend.is_enabled is False
    assert config.log_level == "INFO"
    assert config.kill_switch_key == "f12"
    assert str(config.control_state_path).endswith("data\\runtime\\control_panel_state.json")


def test_load_runtime_config_supports_generic_remote_backend() -> None:
    config = load_runtime_config(
        {
            "GHOST_POKER_CONTROL_MODE": "autonomous",
            "GHOST_POKER_EXECUTION_SAFETY": "armed",
            "GHOST_POKER_META_BACKEND": "openai-compatible",
            "GHOST_POKER_META_MODEL": "gpt-poker-1",
            "GHOST_POKER_META_BASE_URL": "http://localhost:11434/v1",
            "GHOST_POKER_META_API_KEY": "secret-key",
        },
        load_project_dotenv=False,
    )

    assert config.control_mode is ControlMode.AUTONOMOUS
    assert config.execution_safety is ExecutionSafety.ARMED
    assert config.control_gate_mode is ControlGateMode.DISABLED
    assert config.meta_backend.kind is MetaBackendKind.OPENAI_COMPATIBLE
    assert config.meta_backend.model == "gpt-poker-1"
    assert config.meta_backend.base_url == "http://localhost:11434/v1"
    assert config.meta_backend.api_key == "secret-key"
    assert config.meta_backend.is_remote is True


def test_load_runtime_config_can_fallback_to_provider_key() -> None:
    config = load_runtime_config(
        {
            "GHOST_POKER_META_BACKEND": "mistral",
            "MISTRAL_API_KEY": "mistral-secret",
        },
        load_project_dotenv=False,
    )

    assert config.meta_backend.kind is MetaBackendKind.MISTRAL
    assert config.meta_backend.api_key == "mistral-secret"


def test_load_runtime_config_accepts_local_backend_without_api_key() -> None:
    config = load_runtime_config(
        {
            "GHOST_POKER_META_BACKEND": "local",
            "GHOST_POKER_META_MODEL": "llama-poker.gguf",
        },
        load_project_dotenv=False,
    )

    assert config.meta_backend.kind is MetaBackendKind.LOCAL
    assert config.meta_backend.model == "llama-poker.gguf"
    assert config.meta_backend.api_key is None
    assert config.meta_backend.is_remote is False


def test_load_runtime_config_supports_visible_control_gate() -> None:
    config = load_runtime_config(
        {
            "GHOST_POKER_CONTROL_GATE_MODE": "panel",
            "GHOST_POKER_CONTROL_STATE_PATH": "data/runtime/custom_control_state.json",
        },
        load_project_dotenv=False,
    )

    assert config.control_gate_mode is ControlGateMode.PANEL
    assert str(config.control_state_path).endswith("data\\runtime\\custom_control_state.json")
