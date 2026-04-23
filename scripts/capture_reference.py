"""J1.1 — Capture d'une image de référence PokerTH.

Capture l'écran principal et sauvegarde dans data/captures/j1_reference.png.
Usage :
    uv run python scripts/capture_reference.py
"""

import sys
from pathlib import Path

import mss
from loguru import logger


def main() -> int:
    out_dir = Path("data/captures")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "j1_reference.png"

    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            shot = sct.grab(monitor)
            mss.tools.to_png(shot.rgb, shot.size, output=str(out_path))
        logger.success(f"Capture OK ({shot.size}) -> {out_path}")
        return 0
    except Exception as e:  # noqa: BLE001
        logger.error(f"Capture echouee : {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
