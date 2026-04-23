"""J1.2 — Calibration interactive des zones PokerTH.

Capture la fenêtre PokerTH et demande à l'utilisateur de tracer un
rectangle autour de chaque zone d'intérêt. Les zones sont stockées en
coordonnées relatives (0-1) dans data/config/pokerth_layout.json, ce
qui rend la perception adaptative au redimensionnement de la fenêtre.

Usage :
    uv run python scripts/calibrate_layout.py

Commandes OpenCV (fenêtre "Calibration") :
- glisser-déposer pour tracer le rectangle
- Entrée ou Espace pour valider
- 'c' pour annuler la zone courante et recommencer
- Esc pour quitter (progression sauvegardée)
"""

from __future__ import annotations

import sys

import cv2
import numpy as np
from loguru import logger

from ghost_poker.perception.layout import (
    LAYOUT_PATH,
    ZONE_DESCRIPTIONS,
    ZONE_NAMES,
    Layout,
    RelRect,
)
from ghost_poker.perception.window import (
    PokerTHNotFoundError,
    capture_pokerth,
)


def _wrap(text: str, width: int = 70) -> list[str]:
    """Coupe un texte en lignes d'environ `width` caracteres, sans couper les mots."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _render_instruction_panel(idx: int, total: int, zone_name: str, description: str) -> np.ndarray:
    """Construit un panneau d'instructions séparé pour ne pas masquer la table."""
    lines = [
        f"[{idx}/{total}] Zone : {zone_name}",
        *_wrap(description, width=44),
        "",
        "Commandes :",
        "- Drag : tracer la zone",
        "- Entree/Espace : valider",
        "- c : refaire la zone courante",
        "- Esc : quitter et sauvegarder",
    ]

    width = 520
    line_height = 28
    padding = 18
    height = padding * 2 + line_height * len(lines)
    panel = np.full((height, width, 3), 24, dtype=np.uint8)

    cv2.putText(
        panel,
        "Instructions calibration",
        (padding, padding + 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (80, 255, 255),
        2,
        cv2.LINE_AA,
    )

    y = padding + 36
    for line in lines:
        if not line:
            y += 10
            continue
        color = (230, 230, 230)
        scale = 0.55
        thickness = 1
        if line.startswith("["):
            color = (0, 220, 255)
            scale = 0.65
            thickness = 2
        elif line == "Commandes :":
            color = (120, 220, 120)
            scale = 0.58
            thickness = 2
        cv2.putText(
            panel,
            line,
            (padding, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color,
            thickness,
            cv2.LINE_AA,
        )
        y += line_height

    return panel


def calibrate(load_existing: bool = True) -> int:
    try:
        image, rect = capture_pokerth()
    except PokerTHNotFoundError as e:
        logger.error(str(e))
        return 1

    logger.info(f"PokerTH détecté : {rect.width}x{rect.height} @ ({rect.left}, {rect.top})")

    if load_existing and LAYOUT_PATH.exists():
        layout = Layout.load()
        logger.info(f"Layout existant chargé depuis {LAYOUT_PATH} ({len(layout.zones)} zones).")
    else:
        layout = Layout.empty()

    if layout.reference_size is not None and layout.reference_size != (rect.width, rect.height):
        ref_w, ref_h = layout.reference_size
        logger.warning(
            "Taille PokerTH differente de la calibration precedente : "
            f"reference={ref_w}x{ref_h}, actuel={rect.width}x{rect.height}. "
            "Si le layout a bouge, il faut retracer les zones."
        )

    layout.reference_width = rect.width
    layout.reference_height = rect.height

    h, w = image.shape[:2]
    window_name = "Calibration PokerTH"
    help_window_name = "Instructions calibration"

    for idx, zone_name in enumerate(ZONE_NAMES, start=1):
        already = zone_name in layout.zones
        description = ZONE_DESCRIPTIONS.get(zone_name, "")
        tag = "[deja calibre, entree sans drag = garder]" if already else "[a tracer]"
        logger.info(f"[{idx}/{len(ZONE_NAMES)}] {zone_name} {tag}")
        logger.info(f"    {description}")

        # On redessine l'image avec les zones déjà placées pour que
        # l'utilisateur voie sa progression pendant le drag.
        canvas = image.copy()
        for prev_name, prev_rel in layout.zones.items():
            px, py, pw, ph = prev_rel.to_pixels_in(w, h)
            cv2.rectangle(canvas, (px, py), (px + pw, py + ph), (0, 200, 0), 1)
            cv2.putText(
                canvas, prev_name, (px + 2, py + 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 220, 220), 1, cv2.LINE_AA,
            )

        help_panel = _render_instruction_panel(idx, len(ZONE_NAMES), zone_name, description)
        cv2.imshow(help_window_name, help_panel)

        roi = cv2.selectROI(window_name, canvas, showCrosshair=False, fromCenter=False)
        x, y, rw, rh = roi

        if rw == 0 or rh == 0:
            if already:
                logger.info(f"    -> {zone_name} conservee (pas de nouvelle selection).")
                continue
            logger.warning(f"    -> {zone_name} non definie, on passe.")
            continue

        rel = RelRect(x=x / w, y=y / h, w=rw / w, h=rh / h)
        layout.zones[zone_name] = rel
        logger.info(
            f"    -> {zone_name} OK : ({rel.x:.3f}, {rel.y:.3f}, {rel.w:.3f}, {rel.h:.3f})"
        )

    cv2.destroyAllWindows()

    layout.save()
    logger.success(f"Layout sauvegarde : {LAYOUT_PATH} ({len(layout.zones)} zones).")

    if not layout.is_complete:
        missing = [z for z in ZONE_NAMES if z not in layout.zones]
        logger.warning(f"Zones manquantes : {missing}")
        return 2
    return 0


def main() -> int:
    return calibrate()


if __name__ == "__main__":
    sys.exit(main())
