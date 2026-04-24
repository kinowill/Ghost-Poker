from ghost_poker.control import build_control_policy
from ghost_poker.utils.runtime_config import ControlMode


def test_assist_mode_requires_manual_confirmation() -> None:
    policy = build_control_policy(ControlMode.ASSIST)

    assert policy.executes_actions is False
    assert policy.requires_manual_confirmation is True
    assert policy.exposes_recommendations is True


def test_autonomous_mode_executes_actions() -> None:
    policy = build_control_policy(ControlMode.AUTONOMOUS)

    assert policy.executes_actions is True
    assert policy.requires_manual_confirmation is False
