"""Detection simple des touches gardees sous Windows."""

from __future__ import annotations

import ctypes
import sys
from typing import Iterable


_VK_BY_KEY = {
    "f1": 0x70,
    "f2": 0x71,
    "f3": 0x72,
    "f4": 0x73,
    "f5": 0x74,
    "f6": 0x75,
    "f7": 0x76,
    "f8": 0x77,
    "f9": 0x78,
    "f10": 0x79,
    "f11": 0x7A,
    "f12": 0x7B,
    "shift": 0x10,
    "left_shift": 0xA0,
    "right_shift": 0xA1,
    "ctrl": 0x11,
    "control": 0x11,
    "left_ctrl": 0xA2,
    "right_ctrl": 0xA3,
    "alt": 0x12,
    "left_alt": 0xA4,
    "right_alt": 0xA5,
    "space": 0x20,
    "enter": 0x0D,
    "esc": 0x1B,
    "escape": 0x1B,
}


def _normalize_key_name(key_name: str) -> str:
    return key_name.strip().lower().replace("-", "_")


def is_key_pressed(key_name: str) -> bool:
    normalized = _normalize_key_name(key_name)
    if sys.platform != "win32":
        return False

    virtual_key = _VK_BY_KEY.get(normalized)
    if virtual_key is None:
        return False

    state = ctypes.windll.user32.GetAsyncKeyState(virtual_key)
    return bool(state & 0x8000)


def is_supported_key(key_name: str) -> bool:
    return _normalize_key_name(key_name) in _VK_BY_KEY


def get_supported_key_names() -> tuple[str, ...]:
    return tuple(_VK_BY_KEY)


def find_pressed_keys(key_names: Iterable[str] | None = None) -> list[str]:
    names = key_names if key_names is not None else get_supported_key_names()
    pressed: list[str] = []
    for key_name in names:
        normalized = _normalize_key_name(key_name)
        if normalized not in _VK_BY_KEY:
            continue
        if is_key_pressed(normalized):
            pressed.append(normalized)
    return pressed


def is_kill_switch_pressed(key_name: str) -> bool:
    return is_key_pressed(key_name)


def is_supported_function_key(key_name: str) -> bool:
    return is_supported_key(key_name)
