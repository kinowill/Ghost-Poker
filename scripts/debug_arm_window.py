"""Teste la fenetre armee sans dependre d'un spot PokerTH actionnable."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import TextIO

from loguru import logger

from ghost_poker.control.executor import observe_armed_window
from ghost_poker.control.kill_switch import get_supported_key_names, is_supported_key
from ghost_poker.utils import load_runtime_config

DEFAULT_LOG_DIR = Path("data/logs/arm_window")


def _build_log_session(log_root: Path) -> tuple[Path, Path, TextIO]:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    session_dir = log_root / timestamp
    session_dir.mkdir(parents=True, exist_ok=True)
    log_path = session_dir / "result.json"
    handle = log_path.open("w", encoding="utf-8")
    return session_dir, log_path, handle


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Teste la fenetre armee sans PokerTH.")
    parser.add_argument(
        "--delay-ms",
        type=int,
        default=5000,
        help="Duree de la fenetre armee en ms (defaut: 5000).",
    )
    parser.add_argument(
        "--arm-key",
        default="f10",
        help="Touche d'armement a maintenir (defaut: f10).",
    )
    parser.add_argument(
        "--kill-switch-key",
        default=None,
        help="Kill switch a surveiller (defaut: valeur runtime, souvent f12).",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=DEFAULT_LOG_DIR,
        help="Dossier racine des logs (defaut: data/logs/arm_window).",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    runtime_config = load_runtime_config()
    kill_switch_key = args.kill_switch_key or runtime_config.kill_switch_key

    invalid = [
        key for key in (args.arm_key, kill_switch_key)
        if key and not is_supported_key(key)
    ]
    if invalid:
        allowed = ", ".join(get_supported_key_names())
        logger.error(f"Touches non supportees: {', '.join(invalid)}. Valeurs: {allowed}")
        return 1

    session_dir, log_path, log_handle = _build_log_session(args.log_dir)
    logger.info(
        "Test arm_window demarre "
        f"(delay_ms={args.delay_ms}, arm_key={args.arm_key}, kill_switch_key={kill_switch_key})."
    )
    logger.info(
        "Maintiens la touche d'armement pendant toute la fenetre, "
        "ou ajoute le kill switch pour verifier sa priorite."
    )

    result = observe_armed_window(
        armed_delay_ms=args.delay_ms,
        kill_switch_key=kill_switch_key,
        arm_key=args.arm_key,
    )

    logger.info(json.dumps(result, ensure_ascii=False, indent=2))
    log_handle.write(json.dumps(result, ensure_ascii=False, indent=2))
    log_handle.close()
    logger.info(f"Resultat sauvegarde dans {log_path}")
    logger.info(f"Session arm_window sauvegardee dans {session_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
