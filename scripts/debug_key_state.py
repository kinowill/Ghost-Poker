"""Observe quelles touches gardees sont reellement vues par Windows."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import TextIO

from loguru import logger

from ghost_poker.control.kill_switch import (
    find_pressed_keys,
    get_supported_key_names,
    is_supported_key,
)

DEFAULT_KEYS = [
    "f10",
    "f12",
    "shift",
    "right_shift",
    "ctrl",
    "right_ctrl",
    "alt",
    "space",
]
DEFAULT_LOG_DIR = Path("data/logs/key_state")


def _build_log_session(log_root: Path) -> tuple[Path, Path, TextIO]:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    session_dir = log_root / timestamp
    session_dir.mkdir(parents=True, exist_ok=True)
    log_path = session_dir / "events.jsonl"
    handle = log_path.open("a", encoding="utf-8")
    return session_dir, log_path, handle


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Observe quelles touches sont vues par Windows.")
    parser.add_argument(
        "--keys",
        default=",".join(DEFAULT_KEYS),
        help=(
            "Liste comma-separated des touches a observer "
            "(defaut: f10,f12,shift,right_shift,ctrl,right_ctrl,alt,space)."
        ),
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.1,
        help="Delai entre deux lectures (defaut: 0.1s).",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=0,
        help="Nombre max de changements a afficher avant arret (0 = infini).",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=DEFAULT_LOG_DIR,
        help="Dossier racine des logs JSONL (defaut: data/logs/key_state).",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    keys = [item.strip() for item in args.keys.split(",") if item.strip()]
    invalid = [key for key in keys if not is_supported_key(key)]
    if invalid:
        allowed = ", ".join(get_supported_key_names())
        logger.error(f"Touches non supportees: {', '.join(invalid)}. Valeurs: {allowed}")
        return 1

    session_dir, log_path, log_handle = _build_log_session(args.log_dir)
    previous_signature: str | None = None
    emitted_events = 0

    logger.info(
        "Surveillance key_state demarree "
        f"(keys={keys}, interval={args.interval:.2f}s, max_events={args.max_events or 'inf'}). "
        "Ctrl+C pour quitter."
    )
    logger.info(f"Journal auto actif : {log_path}")

    try:
        while True:
            pressed = find_pressed_keys(keys)
            payload = {
                "observed_at": datetime.now().isoformat(timespec="seconds"),
                "pressed_keys": pressed,
            }
            signature = json.dumps(payload["pressed_keys"])
            if signature != previous_signature:
                logger.info(json.dumps(payload, ensure_ascii=False, indent=2))
                log_handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
                log_handle.flush()
                previous_signature = signature
                emitted_events += 1
                if args.max_events and emitted_events >= args.max_events:
                    break

            time.sleep(max(args.interval, 0.05))
    except KeyboardInterrupt:
        logger.info("Surveillance interrompue par l'utilisateur.")
    finally:
        log_handle.close()
        logger.info(f"Session key_state sauvegardee dans {session_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
