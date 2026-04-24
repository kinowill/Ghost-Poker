from unittest.mock import patch

from ghost_poker.control.kill_switch import (
    find_pressed_keys,
    get_supported_key_names,
    is_key_pressed,
    is_supported_key,
)


def test_is_supported_key_accepts_modifier_keys() -> None:
    assert is_supported_key("f10")
    assert is_supported_key("right_shift")
    assert is_supported_key("ctrl")
    assert is_supported_key("space")
    assert not is_supported_key("caps_lock")


def test_get_supported_key_names_exposes_expected_entries() -> None:
    names = get_supported_key_names()

    assert "f12" in names
    assert "right_shift" in names
    assert "ctrl" in names


def test_is_key_pressed_reads_windows_async_state() -> None:
    fake_user32 = type("FakeUser32", (), {"GetAsyncKeyState": lambda self, _: 0x8000})()
    fake_windll = type("FakeWindll", (), {"user32": fake_user32})()

    with (
        patch("ghost_poker.control.kill_switch.sys.platform", "win32"),
        patch("ghost_poker.control.kill_switch.ctypes.windll", fake_windll, create=True),
    ):
        assert is_key_pressed("f10") is True


def test_find_pressed_keys_filters_to_supported_pressed_values() -> None:
    with patch(
        "ghost_poker.control.kill_switch.is_key_pressed",
        side_effect=lambda key: key in {"right_shift", "space"},
    ):
        pressed = find_pressed_keys(["right_shift", "space", "caps_lock"])

    assert pressed == ["right_shift", "space"]
