"""Surveille l'etat de table PokerTH en continu.

Usage :
    uv run python scripts/watch_table_state.py
    uv run python scripts/watch_table_state.py --interval 0.75 --max-events 10
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from loguru import logger

from ghost_poker.perception.layout import LAYOUT_PATH, Layout
from ghost_poker.perception.regions import extract_regions
from ghost_poker.perception.table_state import TableState, read_table_state
from ghost_poker.perception.window import PokerTHNotFoundError, capture_pokerth


def _build_snapshot(state: TableState) -> dict[str, object]:
    hero = state.seats.get(state.hero_seat_name)
    return {
        "street": state.table_meta.street,
        "game_number": state.table_meta.game_number,
        "hand_number": state.table_meta.hand_number,
        "pot_total": state.pot.total,
        "pot_bets": state.pot.bets,
        "hero_name": hero.player_name if hero else None,
        "hero_stack": hero.stack if hero else None,
        "actions": [option.to_dict() for option in state.actions.options],
        "all_in_hotkey": state.actions.all_in_hotkey,
        "presets_percent": state.actions.presets_percent,
        "slider_amount": state.actions.slider_amount,
        "geometry_warning": state.geometry_warning,
    }


def _is_plausible_snapshot(snapshot: dict[str, object]) -> bool:
    """Évite d'émettre des frames OCR polluées pendant la validation."""
    game_number = snapshot.get("game_number")
    hand_number = snapshot.get("hand_number")
    street = snapshot.get("street")
    pot_total = snapshot.get("pot_total")
    pot_bets = snapshot.get("pot_bets")
    hero_name = snapshot.get("hero_name")
    actions = snapshot.get("actions")

    if game_number is None and hand_number is None:
        return False

    if (
        street is None
        and pot_total is None
        and pot_bets is None
        and hero_name not in {None, "Human Player"}
        and not actions
    ):
        return False

    return True


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Observe l'etat de table PokerTH en continu.")
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Delai en secondes entre deux lectures (defaut: 1.0).",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=0,
        help="Nombre maximal de changements a afficher avant arret (0 = infini).",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if not LAYOUT_PATH.exists():
        logger.error(f"Aucun layout calibre : {LAYOUT_PATH} absent. Lance d'abord calibrate_layout.py.")
        return 1

    layout = Layout.load()
    previous_signature: str | None = None
    emitted_events = 0

    logger.info(
        "Surveillance table_state demarree "
        f"(interval={args.interval:.2f}s, max_events={args.max_events or 'inf'}). Ctrl+C pour quitter."
    )

    try:
        while True:
            try:
                image, rect = capture_pokerth()
            except PokerTHNotFoundError as exc:
                logger.error(str(exc))
                return 1

            frame = extract_regions(image, rect, layout)
            state = read_table_state(frame)
            snapshot = _build_snapshot(state)
            if not _is_plausible_snapshot(snapshot):
                time.sleep(max(args.interval, 0.1))
                continue
            signature = json.dumps(snapshot, sort_keys=True)

            if signature != previous_signature:
                logger.info(json.dumps(snapshot, indent=2))
                previous_signature = signature
                emitted_events += 1
                if args.max_events and emitted_events >= args.max_events:
                    break

            time.sleep(max(args.interval, 0.1))
    except KeyboardInterrupt:
        logger.info("Surveillance interrompue par l'utilisateur.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
