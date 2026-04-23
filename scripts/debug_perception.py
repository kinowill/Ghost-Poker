"""J1.3 — Debug de perception à partir du layout validé.

Capture PokerTH, découpe les zones calibrées, sauvegarde les crops et écrit
un résumé JSON pour contrôler la géométrie avant OCR / template matching.

Usage :
    uv run python scripts/debug_perception.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import cv2
from loguru import logger

from ghost_poker.perception.layout import LAYOUT_PATH, Layout
from ghost_poker.perception.regions import extract_regions
from ghost_poker.perception.table_state import read_table_state
from ghost_poker.perception.window import PokerTHNotFoundError, capture_pokerth


def _build_output_dir() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = Path("data/captures/perception_debug") / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def main() -> int:
    if not LAYOUT_PATH.exists():
        logger.error(f"Aucun layout calibré : {LAYOUT_PATH} absent. Lance d'abord calibrate_layout.py.")
        return 1

    layout = Layout.load()

    try:
        image, rect = capture_pokerth()
    except PokerTHNotFoundError as e:
        logger.error(str(e))
        return 1

    frame = extract_regions(image, rect, layout)
    out_dir = _build_output_dir()

    window_path = out_dir / "window.png"
    cv2.imwrite(str(window_path), image)

    zone_artifacts: dict[str, str] = {}
    for name, zone in frame.zones.items():
        zone_path = out_dir / f"{name}.png"
        cv2.imwrite(str(zone_path), zone.crop)
        zone_artifacts[name] = str(zone_path)

    summary = frame.to_dict()
    summary["artifacts"] = {
        "window": str(window_path),
        "zones": zone_artifacts,
    }

    try:
        table_state = read_table_state(frame)
        summary["table_state"] = table_state.to_dict()
    except Exception as e:  # noqa: BLE001
        summary["table_state_error"] = str(e)
        logger.exception("Lecture OCR/etat de table echouee")

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if frame.geometry_warning:
        logger.warning(frame.geometry_warning)

    logger.info(json.dumps(summary, indent=2))
    logger.success(f"Debug perception sauvegardé dans {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
