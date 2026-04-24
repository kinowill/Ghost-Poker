"""J1.2 — Prévisualisation du layout calibré.

Capture la fenêtre PokerTH et dessine par-dessus les rectangles des zones
calibrées pour vérifier que la calibration est correcte.

Usage :
    uv run python scripts/preview_layout.py

Appuyer sur une touche pour fermer.
"""

from __future__ import annotations

import sys

import cv2
from loguru import logger

from ghost_poker.perception.layout import LAYOUT_PATH, Layout
from ghost_poker.perception.window import PokerTHNotFoundError, capture_pokerth


def main() -> int:
    if not LAYOUT_PATH.exists():
        logger.error(
            f"Aucun layout calibré : {LAYOUT_PATH} absent. Lance d'abord calibrate_layout.py."
        )
        return 1

    layout = Layout.load()

    try:
        image, rect = capture_pokerth()
    except PokerTHNotFoundError as e:
        logger.error(str(e))
        return 1

    logger.info(f"Fenêtre PokerTH : {rect.width}x{rect.height}")
    logger.info(f"Zones chargées : {list(layout.zones.keys())}")

    overlay = image.copy()
    h, w = image.shape[:2]
    warning = layout.geometry_warning(w, h)
    if warning:
        logger.warning(warning)
        cv2.rectangle(overlay, (0, 0), (w, 38), (0, 0, 120), thickness=-1)
        cv2.putText(
            overlay,
            "ATTENTION : resize detecte, layout possiblement decale",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

    for name, rel in layout.zones.items():
        x, y, rw, rh = rel.to_pixels_in(w, h)
        cv2.rectangle(overlay, (x, y), (x + rw, y + rh), (0, 255, 0), 2)
        cv2.putText(
            overlay, name, (x + 2, y + 14),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1, cv2.LINE_AA,
        )

    out_path = "data/captures/j1_layout_preview.png"
    cv2.imwrite(out_path, overlay)
    logger.success(f"Aperçu sauvegardé : {out_path}")

    cv2.imshow("Layout preview (appuie sur une touche)", overlay)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
