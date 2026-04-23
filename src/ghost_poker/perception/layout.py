"""Layout PokerTH — définition et persistance des zones d'intérêt.

Une zone est un rectangle *relatif* à la zone client PokerTH
(x, y, w, h entre 0 et 1). Cela permet de rester adaptatif quand la
fenêtre se déplace, et de comparer la taille courante à la taille de
référence utilisée pendant la calibration.

Le layout est sérialisé en JSON dans data/config/pokerth_layout.json.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from ghost_poker.perception.window import WindowRect

LAYOUT_PATH = Path("data/config/pokerth_layout.json")
HERO_SEAT_NAME = "seat_10"

# Ordre canonique des zones à calibrer pour PokerTH 10-max.
# Un siège couvre l'ensemble visuel d'un joueur (nom + stack + cartes).
# On affinera en sous-zones (stack OCR, cards, indicateur actif) après J1.2.
ZONE_NAMES: tuple[str, ...] = (
    "hero_cards",
    "board",
    "table_meta",
    "pot",
    "seat_1",
    "seat_2",
    "seat_3",
    "seat_4",
    "seat_5",
    "seat_6",
    "seat_7",
    "seat_8",
    "seat_9",
    "seat_10",
    "actions",
)

# Description française affichée pendant la calibration.
# Numérotation PokerTH observée sur ce poste : le "Human Player" est Player 10.
ZONE_DESCRIPTIONS: dict[str, str] = {
    "hero_cards": (
        "Tes 2 cartes (celles du 'Human Player', face visible, au siege du bas). "
        "Trace une box serree qui englobe juste les deux cartes."
    ),
    "board": (
        "Le board : les 5 emplacements des cartes communes au centre de la table. "
        "Meme si elles ne sont pas encore sorties, trace la box sur tout le rail horizontal."
    ),
    "table_meta": (
        "Le bloc texte a droite du board qui affiche la street actuelle "
        "(Preflop / Flop / Turn / River) ainsi que 'Game: X' et 'Hand: Y'. "
        "Trace une box sur tout ce bloc texte."
    ),
    "pot": (
        "Le POT : le texte qui affiche le montant du pot au centre de la table "
        "(ex. 'Pot $200'). Box serree sur le texte seulement."
    ),
    "seat_1": "Siege Player 1 : englobe son nom + stack + cartes (ou emplacement si siege vide).",
    "seat_2": "Siege Player 2 : englobe son nom + stack + cartes.",
    "seat_3": "Siege Player 3 : englobe son nom + stack + cartes.",
    "seat_4": "Siege Player 4 : englobe son nom + stack + cartes.",
    "seat_5": "Siege Player 5 : englobe son nom + stack + cartes.",
    "seat_6": "Siege Player 6 : englobe son nom + stack + cartes.",
    "seat_7": "Siege Player 7 : englobe son nom + stack + cartes.",
    "seat_8": "Siege Player 8 : englobe son nom + stack + cartes.",
    "seat_9": "Siege Player 9 : englobe son nom + stack + cartes.",
    HERO_SEAT_NAME: (
        "Siege Player 10 : englobe son nom + stack + cartes "
        "(c'est le Human Player sur ce layout PokerTH)."
    ),
    "actions": (
        "Les boutons d'action (Fold / Check / Call / Raise / All-In) "
        "qui apparaissent en bas quand c'est TON tour de parler. "
        "Box qui englobe toute la rangee de boutons."
    ),
}


@dataclass(frozen=True)
class RelRect:
    """Rectangle en coordonnées relatives (0-1)."""

    x: float
    y: float
    w: float
    h: float

    def to_absolute(self, win: WindowRect) -> tuple[int, int, int, int]:
        """Convertit en (left, top, width, height) en pixels absolus écran."""
        return (
            win.left + int(self.x * win.width),
            win.top + int(self.y * win.height),
            int(self.w * win.width),
            int(self.h * win.height),
        )

    def to_pixels_in(self, width: int, height: int) -> tuple[int, int, int, int]:
        """Convertit en (x, y, w, h) en pixels pour une image de taille donnée."""
        return (
            int(self.x * width),
            int(self.y * height),
            int(self.w * width),
            int(self.h * height),
        )


@dataclass
class Layout:
    """Layout PokerTH — dict de zones relatives, indexé par nom."""

    zones: dict[str, RelRect]
    reference_width: int | None = None
    reference_height: int | None = None

    @property
    def reference_size(self) -> tuple[int, int] | None:
        if self.reference_width is None or self.reference_height is None:
            return None
        return self.reference_width, self.reference_height

    def geometry_warning(self, width: int, height: int) -> str | None:
        """Retourne un warning si la taille courante diverge de la calibration."""
        ref = self.reference_size
        if ref is None:
            return "Layout ancien format : taille de reference absente."

        ref_w, ref_h = ref
        width_delta = abs(width - ref_w) / max(ref_w, 1)
        height_delta = abs(height - ref_h) / max(ref_h, 1)
        aspect_delta = abs((width / max(height, 1)) - (ref_w / max(ref_h, 1)))

        if width_delta <= 0.03 and height_delta <= 0.03 and aspect_delta <= 0.03:
            return None

        return (
            "Layout potentiellement invalide : "
            f"reference={ref_w}x{ref_h}, actuel={width}x{height}. "
            "PokerTH ne garde pas forcement la meme geometrie apres resize."
        )

    @property
    def is_complete(self) -> bool:
        return all(name in self.zones for name in ZONE_NAMES)

    def save(self, path: Path = LAYOUT_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "zones": {name: asdict(rect) for name, rect in self.zones.items()},
            "meta": {
                "reference_width": self.reference_width,
                "reference_height": self.reference_height,
                "hero_seat_name": HERO_SEAT_NAME,
            },
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = LAYOUT_PATH) -> Layout:
        data = json.loads(path.read_text(encoding="utf-8"))
        if "zones" in data:
            zones = {name: RelRect(**rect) for name, rect in data["zones"].items()}
            meta = data.get("meta", {})
            return cls(
                zones=zones,
                reference_width=meta.get("reference_width"),
                reference_height=meta.get("reference_height"),
            )

        # Compat rétro : ancien format = dict brut de zones sans métadonnées.
        zones = {name: RelRect(**rect) for name, rect in data.items()}
        return cls(zones=zones)

    @classmethod
    def empty(cls) -> Layout:
        return cls(zones={})
