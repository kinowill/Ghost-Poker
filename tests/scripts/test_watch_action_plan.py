from pathlib import Path
from unittest.mock import patch

from ghost_poker.orchestrator import build_runtime_profile
from ghost_poker.perception.table_state import (
    ActionOption,
    ActionsState,
    PotState,
    TableMetaState,
    TableState,
)
from ghost_poker.utils import load_runtime_config
from scripts.watch_action_plan import (
    _build_log_record,
    _build_log_session,
    _build_payload,
    _pick_preview_decision,
    _resolve_decision,
)


def _sample_table_state() -> TableState:
    return TableState(
        hero_seat_name="seat_10",
        geometry_warning=None,
        hero_cards_text=None,
        board_texts=[],
        table_meta=TableMetaState(raw_lines=[], street="Flop", game_number=2, hand_number=7),
        pot=PotState(raw_lines=[], total=400, bets=0),
        actions=ActionsState(
            raw_lines=[],
            slider_amount=20,
            presets_percent=[33, 50, 100],
            all_in_hotkey="F4",
            options=[
                ActionOption(label="Bet", hotkey="F3", amount=20),
                ActionOption(label="Check", hotkey="F2", amount=None),
                ActionOption(label="Fold", hotkey="F1", amount=None),
            ],
        ),
        seats={},
        raw_zone_ocr={},
    )


def test_pick_preview_decision_prefers_check() -> None:
    decision = _pick_preview_decision(_sample_table_state())

    assert decision is not None
    assert decision.kind.value == "check"
    assert decision.reasoning == "preview_heuristic"


def test_resolve_decision_can_force_raise_amount() -> None:
    decision, source = _resolve_decision("raise", 120, _sample_table_state())

    assert decision is not None
    assert decision.kind.value == "raise"
    assert decision.amount == 120
    assert source == "forced_cli_decision"


def test_build_payload_without_decision_exposes_warning() -> None:
    profile = build_runtime_profile(load_runtime_config({}, load_project_dotenv=False))
    payload = _build_payload(
        profile,
        _sample_table_state(),
        None,
        "preview_heuristic",
        armed_delay_ms=0,
        arm_key=None,
    )

    assert payload["action_plan"] is None
    assert payload["execution_result"] is None
    assert payload["warnings"] == ["aucune decision preview possible avec les actions visibles"]


def test_build_payload_includes_dry_run_execution_result() -> None:
    profile = build_runtime_profile(
        load_runtime_config(
            {
                "GHOST_POKER_CONTROL_MODE": "autonomous",
                "GHOST_POKER_EXECUTION_SAFETY": "dry_run",
            },
            load_project_dotenv=False,
        )
    )
    decision = _pick_preview_decision(_sample_table_state())
    payload = _build_payload(
        profile,
        _sample_table_state(),
        decision,
        "preview_heuristic",
        armed_delay_ms=0,
        arm_key=None,
    )

    assert payload["action_plan"] is not None
    assert payload["execution_result"]["status"] == "dry_run"


def test_build_log_session_creates_jsonl_target() -> None:
    fake_root = Path("data/logs/action_plan")
    fake_handle = object()

    with (
        patch.object(Path, "mkdir") as mkdir_mock,
        patch.object(Path, "open", return_value=fake_handle) as open_mock,
    ):
        session_dir, log_path, handle = _build_log_session(fake_root)

    mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
    open_mock.assert_called_once_with("a", encoding="utf-8")
    assert session_dir.parent == fake_root
    assert log_path.parent == session_dir
    assert log_path.name == "events.jsonl"
    assert handle is fake_handle


def test_build_log_record_wraps_payload_with_metadata() -> None:
    record = _build_log_record({"execution_result": {"status": "dry_run"}}, 4)

    assert record["event_index"] == 4
    assert record["payload"] == {"execution_result": {"status": "dry_run"}}
    assert isinstance(record["observed_at"], str)
