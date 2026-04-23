"""Détection et capture adaptative de la fenêtre PokerTH.

On cherche la fenêtre par titre (PokerTH). On retourne le rectangle de
sa zone client réelle en coordonnées écran, puis on capture uniquement
ce contenu-là.

Toutes les zones d'intérêt sont ensuite exprimées en coordonnées
*relatives* à cette zone client (ratios 0-1), pour rester adaptatif
quand la fenêtre se déplace et pour limiter les décalages liés aux
bordures et à la barre de titre.
"""

from __future__ import annotations

import ctypes
import time
from dataclasses import dataclass
from ctypes import wintypes

import mss
import numpy as np
import pygetwindow as gw

# On matche sur le *début* du titre pour éviter de capturer un terminal, un
# navigateur ou un éditeur dont le titre contient accidentellement "PokerTH".
POKERTH_TITLE_PREFIX = "PokerTH"
_SW_RESTORE = 9


@dataclass(frozen=True)
class WindowRect:
    """Rectangle de fenêtre en coordonnées écran absolues."""

    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


class PokerTHNotFoundError(RuntimeError):
    """Aucune fenêtre PokerTH visible."""


def _get_client_rect(win: object) -> WindowRect:
    """Retourne le rectangle écran de la zone client Win32.

    On évite le rectangle de fenêtre complet, car ses bordures et sa barre
    de titre ne suivent pas la même logique de redimensionnement que le
    contenu de jeu.
    """
    hwnd = getattr(win, "_hWnd", None)
    if hwnd is None:
        raise PokerTHNotFoundError("Handle Win32 PokerTH introuvable.")

    user32 = ctypes.windll.user32
    client = wintypes.RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(client)):
        raise PokerTHNotFoundError("Impossible de lire la zone client PokerTH.")

    top_left = wintypes.POINT(0, 0)
    bottom_right = wintypes.POINT(client.right, client.bottom)
    if not user32.ClientToScreen(hwnd, ctypes.byref(top_left)):
        raise PokerTHNotFoundError("Impossible de convertir le coin haut-gauche PokerTH.")
    if not user32.ClientToScreen(hwnd, ctypes.byref(bottom_right)):
        raise PokerTHNotFoundError("Impossible de convertir le coin bas-droit PokerTH.")

    width = bottom_right.x - top_left.x
    height = bottom_right.y - top_left.y
    if width <= 0 or height <= 0:
        raise PokerTHNotFoundError("Zone client PokerTH invalide.")

    return WindowRect(left=top_left.x, top=top_left.y, width=width, height=height)


def _select_pokerth_window() -> object:
    """Retourne la meilleure fenêtre PokerTH candidate."""
    candidates = [
        w for w in gw.getAllWindows()
        if w.title.startswith(POKERTH_TITLE_PREFIX) and w.visible
    ]
    if not candidates:
        raise PokerTHNotFoundError(
            "Aucune fenêtre PokerTH trouvée. Lance PokerTH et démarre une partie."
        )
    # Si plusieurs, on prend la plus grande (évite un éventuel dialogue de config).
    win = max(candidates, key=lambda w: w.width * w.height)
    if win.isMinimized:
        raise PokerTHNotFoundError("Fenêtre PokerTH minimisée.")
    return win


def _focus_window(win: object) -> None:
    """Tente de remettre PokerTH au premier plan avant capture écran."""
    hwnd = getattr(win, "_hWnd", None)
    if hwnd is None:
        return

    user32 = ctypes.windll.user32
    user32.ShowWindow(hwnd, _SW_RESTORE)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.15)


def find_pokerth_window() -> WindowRect:
    """Retourne le rectangle écran de la zone client PokerTH active.

    Lève PokerTHNotFoundError si aucune fenêtre ne correspond ou si
    la fenêtre est minimisée.
    """
    win = _select_pokerth_window()
    return _get_client_rect(win)


def capture_window(rect: WindowRect) -> np.ndarray:
    """Capture le contenu d'un rectangle écran. Retourne un array BGR (H, W, 3)."""
    with mss.mss() as sct:
        monitor = {
            "left": rect.left,
            "top": rect.top,
            "width": rect.width,
            "height": rect.height,
        }
        shot = sct.grab(monitor)
    # mss renvoie BGRA ; on convertit en BGR pour OpenCV.
    arr = np.array(shot, dtype=np.uint8)[:, :, :3]
    return arr


def capture_pokerth() -> tuple[np.ndarray, WindowRect]:
    """Trouve PokerTH et capture son contenu. Retourne (image BGR, rect)."""
    win = _select_pokerth_window()
    _focus_window(win)
    rect = _get_client_rect(win)
    image = capture_window(rect)
    return image, rect
