from ghost_poker.brain import DecisionIntent, DecisionKind
from ghost_poker.orchestrator import build_action_plan, build_runtime_profile
from ghost_poker.perception.table_state import (
    ActionOption,
    ActionsState,
    PotState,
    TableMetaState,
    TableState,
)
from ghost_poker.utils import load_runtime_config


def _sample_table_state() -> TableState:
    return TableState(
        hero_seat_name="seat_10",
        geometry_warning=None,
        hero_cards_text=None,
        board_texts=[],
        table_meta=TableMetaState(raw_lines=[], street="Turn", game_number=1, hand_number=4),
        pot=PotState(raw_lines=[], total=600, bets=200),
        actions=ActionsState(
            raw_lines=[],
            slider_amount=80,
            presets_percent=[33, 50, 100],
            all_in_hotkey="F4",
            options=[
                ActionOption(label="Raise", hotkey="F3", amount=80),
                ActionOption(label="Call", hotkey="F2", amount=40),
                ActionOption(label="Fold", hotkey="F1", amount=None),
            ],
        ),
        seats={},
        raw_zone_ocr={},
    )


def test_build_action_plan_in_assist_mode_requires_confirmation() -> None:
    profile = build_runtime_profile(
        load_runtime_config({"GHOST_POKER_CONTROL_MODE": "assist"}, load_project_dotenv=False)
    )
    plan = build_action_plan(
        runtime_profile=profile,
        table_state=_sample_table_state(),
        decision=DecisionIntent(kind=DecisionKind.CALL),
    )

    assert plan.should_execute is False
    assert plan.requires_manual_confirmation is True
    assert plan.is_actionable is True
    assert plan.target is not None
    assert plan.target.label == "Call"
    assert plan.target.hotkey == "F2"


def test_build_action_plan_in_autonomous_mode_sets_execution_flag() -> None:
    profile = build_runtime_profile(
        load_runtime_config(
            {"GHOST_POKER_CONTROL_MODE": "autonomous"},
            load_project_dotenv=False,
        )
    )
    plan = build_action_plan(
        runtime_profile=profile,
        table_state=_sample_table_state(),
        decision=DecisionIntent(kind=DecisionKind.ALL_IN),
    )

    assert plan.should_execute is True
    assert plan.requires_manual_confirmation is False
    assert plan.target is not None
    assert plan.target.label == "All-In"
    assert plan.target.hotkey == "F4"


def test_build_action_plan_can_request_slider_override_for_raise_amount() -> None:
    profile = build_runtime_profile(load_runtime_config({}, load_project_dotenv=False))
    plan = build_action_plan(
        runtime_profile=profile,
        table_state=_sample_table_state(),
        decision=DecisionIntent(kind=DecisionKind.RAISE, amount=120),
    )

    assert plan.is_actionable is True
    assert plan.target is not None
    assert plan.target.uses_slider is True
    assert plan.target.amount == 120
    assert any("override slider" in warning for warning in plan.warnings)


def test_build_action_plan_blocks_missing_action() -> None:
    profile = build_runtime_profile(load_runtime_config({}, load_project_dotenv=False))
    plan = build_action_plan(
        runtime_profile=profile,
        table_state=_sample_table_state(),
        decision=DecisionIntent(kind=DecisionKind.CHECK),
    )

    assert plan.is_actionable is False
    assert plan.target is None
    assert "action 'Check' indisponible dans l'etat courant" in plan.blocking_issues
