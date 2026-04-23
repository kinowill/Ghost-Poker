"""Première lecture structurée de la table PokerTH."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ghost_poker.perception.layout import HERO_SEAT_NAME
from ghost_poker.perception.ocr import OCRLine, read_ocr_lines
from ghost_poker.perception.regions import PerceptionFrame, ZoneCapture

_DOLLAR_AMOUNT_RE = re.compile(r"\$\s*([0-9][0-9 ]*)")
_GENERIC_AMOUNT_RE = re.compile(r"([0-9][0-9 ]*)")
_ACTION_LABELS = {"fold", "check", "call", "raise", "bet"}
_HOTKEY_RE = re.compile(r"^F\d+$", re.IGNORECASE)
_PERCENT_RE = re.compile(r"^(\d{1,3})%$")
_PLAYER_NAME_RE = re.compile(r"^(human player|player \d+)$", re.IGNORECASE)
_HERO_PLAYER_NAME = "Human Player"
_IGNORED_NAME_TOKENS = {
    "dealer",
    "small",
    "big",
    "blind",
    "call",
    "check",
    "fold",
    "raise",
    "bet",
    "all-in",
}


def _extract_dollar_amount(text: str) -> int | None:
    match = _DOLLAR_AMOUNT_RE.search(text)
    if not match:
        return None
    return int(match.group(1).replace(" ", ""))


def _extract_generic_amount(text: str) -> int | None:
    match = _GENERIC_AMOUNT_RE.search(text)
    if not match:
        return None
    return int(match.group(1).replace(" ", ""))


def _is_probable_player_name(text: str) -> bool:
    if _extract_dollar_amount(text) is not None:
        return False
    lowered = text.strip().lower()
    if lowered in _IGNORED_NAME_TOKENS:
        return False
    upper = text.upper().replace(" ", "")
    if len(upper) <= 3 and all(ch in "23456789TJQKA" for ch in upper):
        return False
    return any(ch.isalpha() for ch in text)


@dataclass
class ActionOption:
    label: str
    hotkey: str | None = None
    amount: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "hotkey": self.hotkey,
            "amount": self.amount,
        }


@dataclass
class PotState:
    raw_lines: list[OCRLine]
    total: int | None = None
    bets: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_lines": [line.to_dict() for line in self.raw_lines],
            "total": self.total,
            "bets": self.bets,
        }


@dataclass
class TableMetaState:
    raw_lines: list[OCRLine]
    street: str | None = None
    game_number: int | None = None
    hand_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_lines": [line.to_dict() for line in self.raw_lines],
            "street": self.street,
            "game_number": self.game_number,
            "hand_number": self.hand_number,
        }


@dataclass
class ActionsState:
    raw_lines: list[OCRLine]
    slider_amount: int | None = None
    presets_percent: list[int] = field(default_factory=list)
    all_in_hotkey: str | None = None
    options: list[ActionOption] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_lines": [line.to_dict() for line in self.raw_lines],
            "slider_amount": self.slider_amount,
            "presets_percent": self.presets_percent,
            "all_in_hotkey": self.all_in_hotkey,
            "options": [option.to_dict() for option in self.options],
        }


@dataclass
class SeatState:
    seat_name: str
    raw_lines: list[OCRLine]
    player_name: str | None = None
    stack: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "seat_name": self.seat_name,
            "raw_lines": [line.to_dict() for line in self.raw_lines],
            "player_name": self.player_name,
            "stack": self.stack,
        }


@dataclass
class TableState:
    hero_seat_name: str
    geometry_warning: str | None
    hero_cards_text: str | None
    board_texts: list[str]
    table_meta: TableMetaState
    pot: PotState
    actions: ActionsState
    seats: dict[str, SeatState]
    raw_zone_ocr: dict[str, list[OCRLine]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "hero_seat_name": self.hero_seat_name,
            "geometry_warning": self.geometry_warning,
            "hero_cards_text": self.hero_cards_text,
            "board_texts": self.board_texts,
            "table_meta": self.table_meta.to_dict(),
            "pot": self.pot.to_dict(),
            "actions": self.actions.to_dict(),
            "seats": {name: seat.to_dict() for name, seat in self.seats.items()},
            "raw_zone_ocr": {
                name: [line.to_dict() for line in lines]
                for name, lines in self.raw_zone_ocr.items()
            },
        }


def _lines_to_texts(lines: list[OCRLine]) -> list[str]:
    return [line.text for line in lines]


def _line_center_y(line: OCRLine) -> float:
    return line.top + (line.height / 2)


def _line_center_x(line: OCRLine) -> float:
    return line.left + (line.width / 2)


def _parse_pot(lines: list[OCRLine]) -> PotState:
    state = PotState(raw_lines=lines)
    for text in _lines_to_texts(lines):
        lower = text.lower()
        if lower.startswith("total"):
            state.total = _extract_dollar_amount(text)
        elif lower.startswith("bets"):
            state.bets = _extract_dollar_amount(text)
    return state


def _parse_table_meta(lines: list[OCRLine]) -> TableMetaState:
    state = TableMetaState(raw_lines=lines)
    for text in _lines_to_texts(lines):
        lowered = text.lower().strip()
        if lowered in {"preflop", "flop", "turn", "river", "showdown"}:
            state.street = text
            continue
        if lowered.startswith("game"):
            match = re.search(r"(\d+)", text)
            if match:
                state.game_number = int(match.group(1))
            continue
        if lowered.startswith("hand"):
            match = re.search(r"(\d+)", text)
            if match:
                state.hand_number = int(match.group(1))
    return state


def _parse_actions(lines: list[OCRLine]) -> ActionsState:
    state = ActionsState(raw_lines=lines)
    hotkeys = [line for line in lines if _HOTKEY_RE.fullmatch(line.text.strip())]
    percentages = []
    amounts = []
    labels = []
    all_in_line: OCRLine | None = None

    for line in lines:
        text = line.text.strip()
        percent_match = _PERCENT_RE.fullmatch(text)
        if percent_match:
            percentages.append((line.left, int(percent_match.group(1))))
            continue

        if _HOTKEY_RE.fullmatch(text):
            continue

        if text.lower() == "all-in":
            all_in_line = line
            continue

        if text.lower() in _ACTION_LABELS:
            labels.append(line)
            continue

        money_value = _extract_dollar_amount(text)
        if money_value is not None:
            amounts.append((line, money_value))
            continue

        generic_amount = _extract_generic_amount(text)
        if generic_amount is not None:
            amounts.append((line, generic_amount))

    percentages.sort(key=lambda item: item[0])
    state.presets_percent = [value for _, value in percentages]

    remaining_hotkeys = hotkeys[:]
    remaining_amounts = amounts[:]

    def claim_hotkey(anchor: OCRLine, max_y_delta: float = 18.0) -> str | None:
        best_index: int | None = None
        best_score: tuple[float, float] | None = None
        anchor_y = _line_center_y(anchor)
        anchor_x = _line_center_x(anchor)

        for index, line in enumerate(remaining_hotkeys):
            delta_y = abs(_line_center_y(line) - anchor_y)
            if delta_y > max_y_delta:
                continue
            delta_x = abs(_line_center_x(line) - anchor_x)
            score = (delta_y, delta_x)
            if best_score is None or score < best_score:
                best_index = index
                best_score = score

        if best_index is None:
            return None
        return remaining_hotkeys.pop(best_index).text.strip().upper()

    def claim_amount(anchor: OCRLine, max_y_delta: float = 24.0) -> int | None:
        best_index: int | None = None
        best_score: tuple[float, float] | None = None
        anchor_y = _line_center_y(anchor)
        anchor_x = _line_center_x(anchor)

        for index, (line, value) in enumerate(remaining_amounts):
            delta_y = _line_center_y(line) - anchor_y
            if delta_y < 0 or delta_y > max_y_delta:
                continue
            delta_x = abs(_line_center_x(line) - anchor_x)
            score = (delta_y, delta_x)
            if best_score is None or score < best_score:
                best_index = index
                best_score = score

        if best_index is None:
            return None
        _, value = remaining_amounts.pop(best_index)
        return value

    if all_in_line is not None:
        state.all_in_hotkey = claim_hotkey(all_in_line)

    labels.sort(key=lambda line: line.top)
    for line in labels:
        state.options.append(
            ActionOption(
                label=line.text.strip(),
                hotkey=claim_hotkey(line),
                amount=claim_amount(line),
            )
        )

    if remaining_amounts:
        _, state.slider_amount = remaining_amounts[0]

    return state


def _parse_seat(seat_name: str, lines: list[OCRLine]) -> SeatState:
    state = SeatState(seat_name=seat_name, raw_lines=lines)
    preferred_names: list[tuple[OCRLine, str]] = []
    fallback_names: list[tuple[OCRLine, str]] = []
    stack_candidates: list[tuple[OCRLine, int]] = []
    selected_name_line: OCRLine | None = None

    for line in lines:
        text = line.text.strip()
        money = _extract_dollar_amount(text)
        if money is not None:
            stack_candidates.append((line, money))
            continue

        if not _is_probable_player_name(text):
            continue

        normalized = text
        if _PLAYER_NAME_RE.fullmatch(normalized):
            preferred_names.append((line, normalized))
        else:
            fallback_names.append((line, normalized))

    if preferred_names:
        selected_name_line, state.player_name = preferred_names[0]
    elif fallback_names:
        fallback_names.sort(key=lambda item: len(item[1]), reverse=True)
        selected_name_line, state.player_name = fallback_names[0]

    if stack_candidates:
        if selected_name_line is None:
            _, state.stack = max(stack_candidates, key=lambda item: item[1])
        else:
            def stack_score(item: tuple[OCRLine, int]) -> tuple[float, float]:
                line, _ = item
                delta_y = abs(_line_center_y(line) - _line_center_y(selected_name_line))
                delta_x = abs(_line_center_x(line) - _line_center_x(selected_name_line))
                return (delta_y, delta_x)

            _, state.stack = min(stack_candidates, key=stack_score)

    if seat_name == HERO_SEAT_NAME:
        state.player_name = _HERO_PLAYER_NAME

    return state


def _ocr_zone(zone_name: str, zone: ZoneCapture) -> list[OCRLine]:
    if zone_name in {"hero_cards", "board"}:
        return []
    return read_ocr_lines(zone.crop)


def read_table_state(frame: PerceptionFrame) -> TableState:
    """Lit une première version structurée de l'état de table."""
    zone_ocr = {name: _ocr_zone(name, zone) for name, zone in frame.zones.items()}

    hero_cards_lines = zone_ocr.get("hero_cards", [])
    board_lines = zone_ocr.get("board", [])
    table_meta_lines = zone_ocr.get("table_meta", [])
    pot_lines = zone_ocr.get("pot", [])
    actions_lines = zone_ocr.get("actions", [])

    seats = {
        name: _parse_seat(name, lines)
        for name, lines in zone_ocr.items()
        if name.startswith("seat_")
    }

    hero_cards_text = " ".join(_lines_to_texts(hero_cards_lines)) or None
    board_texts = _lines_to_texts(board_lines)

    return TableState(
        hero_seat_name=frame.hero_seat_name,
        geometry_warning=frame.geometry_warning,
        hero_cards_text=hero_cards_text,
        board_texts=board_texts,
        table_meta=_parse_table_meta(table_meta_lines),
        pot=_parse_pot(pot_lines),
        actions=_parse_actions(actions_lines),
        seats=seats,
        raw_zone_ocr=zone_ocr,
    )
