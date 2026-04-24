"""Observe la table en direct et construit un ActionPlan preview.

Usage :
    uv run python scripts/watch_action_plan.py
    uv run python scripts/watch_action_plan.py --decision call --max-events 1
    uv run python scripts/watch_action_plan.py --decision call --armed-delay-ms 3000
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import TextIO

from loguru import logger

from ghost_poker.brain import DecisionIntent, DecisionKind
from ghost_poker.control.executor import execute_action_plan
from ghost_poker.control.kill_switch import get_supported_key_names, is_supported_key
from ghost_poker.orchestrator import RuntimeProfile, build_action_plan, build_runtime_profile
from ghost_poker.perception.layout import LAYOUT_PATH, Layout
from ghost_poker.perception.regions import extract_regions
from ghost_poker.perception.table_state import TableState, read_table_state
from ghost_poker.perception.window import PokerTHNotFoundError, capture_pokerth
from ghost_poker.utils import load_runtime_config

DEFAULT_LOG_DIR = Path("data/logs/action_plan")


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
        "slider_amount": state.actions.slider_amount,
        "geometry_warning": state.geometry_warning,
    }


def _is_plausible_snapshot(snapshot: dict[str, object]) -> bool:
    if snapshot.get("game_number") is None and snapshot.get("hand_number") is None:
        return False

    actions = snapshot.get("actions")
    return bool(actions or snapshot.get("all_in_hotkey") is not None or snapshot.get("street"))


def _pick_preview_decision(table_state: TableState) -> DecisionIntent | None:
    options_by_label = {
        option.label.strip().lower(): option
        for option in table_state.actions.options
    }

    for label in ("check", "call", "fold", "bet", "raise"):
        option = options_by_label.get(label)
        if option is None:
            continue
        return DecisionIntent(
            kind=DecisionKind(label),
            amount=option.amount,
            reasoning="preview_heuristic",
        )

    if table_state.actions.all_in_hotkey:
        return DecisionIntent(
            kind=DecisionKind.ALL_IN,
            reasoning="preview_heuristic",
        )

    return None


def _build_log_session(log_root: Path) -> tuple[Path, Path, TextIO]:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    session_dir = log_root / timestamp
    session_dir.mkdir(parents=True, exist_ok=True)
    log_path = session_dir / "events.jsonl"
    handle = log_path.open("a", encoding="utf-8")
    return session_dir, log_path, handle


def _build_log_record(payload: dict[str, object], event_index: int) -> dict[str, object]:
    return {
        "observed_at": datetime.now().isoformat(timespec="seconds"),
        "event_index": event_index,
        "payload": payload,
    }


def _resolve_decision(
    decision_name: str,
    amount: int | None,
    table_state: TableState,
) -> tuple[DecisionIntent | None, str]:
    if decision_name == "auto":
        return _pick_preview_decision(table_state), "preview_heuristic"

    decision_kind = DecisionKind(decision_name)
    return (
        DecisionIntent(
            kind=decision_kind,
            amount=amount,
            reasoning="forced_cli_decision",
        ),
        "forced_cli_decision",
    )


def _build_payload(
    runtime_profile: RuntimeProfile,
    table_state: TableState,
    decision: DecisionIntent | None,
    decision_source: str,
    *,
    armed_delay_ms: int,
    arm_key: str | None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "runtime_profile": runtime_profile.to_dict(),
        "table_state": _build_snapshot(table_state),
        "decision_source": decision_source,
        "decision": decision.to_dict() if decision else None,
    }

    if decision is None:
        payload["action_plan"] = None
        payload["execution_result"] = None
        payload["warnings"] = ["aucune decision preview possible avec les actions visibles"]
        return payload

    action_plan = build_action_plan(runtime_profile, table_state, decision)
    payload["action_plan"] = action_plan.to_dict()
    execution_result = execute_action_plan(
        action_plan,
        execution_safety=runtime_profile.runtime_config.execution_safety,
        kill_switch_key=runtime_profile.runtime_config.kill_switch_key,
        armed_delay_ms=armed_delay_ms,
        arm_key=arm_key,
        control_gate_mode=runtime_profile.runtime_config.control_gate_mode,
        control_state_path=runtime_profile.runtime_config.control_state_path,
    )
    payload["execution_result"] = execution_result.to_dict()
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Observe la table et construit un ActionPlan preview."
    )
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
    parser.add_argument(
        "--decision",
        choices=["auto", "fold", "check", "call", "bet", "raise", "all_in"],
        default="auto",
        help="Decision preview a injecter (defaut: auto heuristique).",
    )
    parser.add_argument(
        "--amount",
        type=int,
        default=None,
        help="Montant a utiliser avec bet/raise quand on force une decision.",
    )
    parser.add_argument(
        "--armed-delay-ms",
        type=int,
        default=0,
        help="Delai avant execution reelle en mode armed (defaut: 0).",
    )
    parser.add_argument(
        "--arm-key",
        default=None,
        help=(
            "Touche a maintenir pendant le delai arme pour autoriser l'envoi "
            "(ex: right_shift, ctrl, f10)."
        ),
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=DEFAULT_LOG_DIR,
        help="Dossier racine des logs JSONL (defaut: data/logs/action_plan).",
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="Desactive l'ecriture du journal JSONL.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if not LAYOUT_PATH.exists():
        logger.error(
            f"Aucun layout calibre : {LAYOUT_PATH} absent. Lance d'abord calibrate_layout.py."
        )
        return 1

    if args.amount is not None and args.decision not in {"bet", "raise"}:
        logger.error("--amount est reserve aux decisions bet/raise.")
        return 1

    if args.arm_key is not None and not is_supported_key(args.arm_key):
        allowed = ", ".join(get_supported_key_names())
        logger.error(f"--arm-key doit etre une touche supportee. Valeurs: {allowed}")
        return 1

    layout = Layout.load()
    runtime_profile = build_runtime_profile(load_runtime_config())
    previous_signature: str | None = None
    emitted_events = 0
    session_dir: Path | None = None
    log_path: Path | None = None
    log_handle: TextIO | None = None

    if not args.no_log:
        session_dir, log_path, log_handle = _build_log_session(args.log_dir)

    logger.info(
        "Surveillance action_plan demarree "
        f"(interval={args.interval:.2f}s, max_events={args.max_events or 'inf'}, "
        f"decision={args.decision}, armed_delay_ms={args.armed_delay_ms}, "
        f"arm_key={args.arm_key or 'none'}). "
        "Ctrl+C pour quitter."
    )
    if log_path is not None:
        logger.info(f"Journal auto actif : {log_path}")

    try:
        while True:
            try:
                image, rect = capture_pokerth()
            except PokerTHNotFoundError as exc:
                logger.error(str(exc))
                return 1

            frame = extract_regions(image, rect, layout)
            table_state = read_table_state(frame)
            snapshot = _build_snapshot(table_state)
            if not _is_plausible_snapshot(snapshot):
                time.sleep(max(args.interval, 0.1))
                continue

            decision, decision_source = _resolve_decision(args.decision, args.amount, table_state)
            payload = _build_payload(
                runtime_profile,
                table_state,
                decision,
                decision_source,
                armed_delay_ms=args.armed_delay_ms,
                arm_key=args.arm_key,
            )
            signature = json.dumps(payload, sort_keys=True)

            if signature != previous_signature:
                logger.info(json.dumps(payload, indent=2))
                previous_signature = signature
                emitted_events += 1
                if log_handle is not None:
                    record = _build_log_record(payload, emitted_events)
                    log_handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                    log_handle.flush()
                if args.max_events and emitted_events >= args.max_events:
                    break

            time.sleep(max(args.interval, 0.1))
    except KeyboardInterrupt:
        logger.info("Surveillance interrompue par l'utilisateur.")
    finally:
        if log_handle is not None:
            log_handle.close()
        if session_dir is not None:
            logger.info(f"Session action_plan sauvegardee dans {session_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
