from pathlib import Path
from unittest.mock import patch

from scripts.watch_table_state import _build_log_record, _build_log_session


def test_build_log_session_creates_jsonl_target() -> None:
    fake_root = Path("data/logs/table_state")
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


def test_build_log_record_wraps_snapshot_with_metadata() -> None:
    record = _build_log_record({"hand_number": 3, "street": "Turn"}, 7)

    assert record["event_index"] == 7
    assert record["snapshot"] == {"hand_number": 3, "street": "Turn"}
    assert isinstance(record["observed_at"], str)
