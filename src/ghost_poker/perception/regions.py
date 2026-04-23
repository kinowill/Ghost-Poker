"""Extraction des zones calibrées depuis une capture PokerTH."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from ghost_poker.perception.layout import HERO_SEAT_NAME, Layout, RelRect
from ghost_poker.perception.window import WindowRect


@dataclass(frozen=True)
class ImageRect:
    """Rectangle en pixels relatif à l'image capturée."""

    x: int
    y: int
    width: int
    height: int

    def as_dict(self) -> dict[str, int]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


@dataclass
class ZoneCapture:
    """Une zone calibrée extraite de la capture courante."""

    name: str
    relative_rect: RelRect
    image_rect: ImageRect
    screen_rect: WindowRect
    crop: np.ndarray

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_rect": {
                "x": round(self.relative_rect.x, 6),
                "y": round(self.relative_rect.y, 6),
                "w": round(self.relative_rect.w, 6),
                "h": round(self.relative_rect.h, 6),
            },
            "image_rect": self.image_rect.as_dict(),
            "screen_rect": {
                "left": self.screen_rect.left,
                "top": self.screen_rect.top,
                "width": self.screen_rect.width,
                "height": self.screen_rect.height,
            },
            "crop_shape": list(self.crop.shape),
        }


@dataclass
class PerceptionFrame:
    """Capture structurée d'un instant PokerTH."""

    window_rect: WindowRect
    image_shape: tuple[int, int, int]
    hero_seat_name: str
    geometry_warning: str | None
    zones: dict[str, ZoneCapture]

    def to_dict(self) -> dict[str, Any]:
        height, width = self.image_shape[:2]
        channels = self.image_shape[2] if len(self.image_shape) > 2 else 1
        return {
            "window_rect": {
                "left": self.window_rect.left,
                "top": self.window_rect.top,
                "width": self.window_rect.width,
                "height": self.window_rect.height,
            },
            "image_shape": {
                "width": width,
                "height": height,
                "channels": channels,
            },
            "hero_seat_name": self.hero_seat_name,
            "geometry_warning": self.geometry_warning,
            "zones": {name: zone.to_dict() for name, zone in self.zones.items()},
        }


def _clip_rect(rel_rect: RelRect, width: int, height: int) -> ImageRect:
    """Convertit un RelRect en pixels image en restant dans les bornes."""
    x, y, crop_w, crop_h = rel_rect.to_pixels_in(width, height)

    x = max(0, min(x, width - 1))
    y = max(0, min(y, height - 1))
    crop_w = max(1, min(crop_w, width - x))
    crop_h = max(1, min(crop_h, height - y))

    return ImageRect(x=x, y=y, width=crop_w, height=crop_h)


def extract_regions(image: np.ndarray, window_rect: WindowRect, layout: Layout) -> PerceptionFrame:
    """Extrait toutes les zones calibrées depuis une capture BGR PokerTH."""
    height, width = image.shape[:2]
    geometry_warning = layout.geometry_warning(width, height)
    zones: dict[str, ZoneCapture] = {}

    for name, rel_rect in layout.zones.items():
        image_rect = _clip_rect(rel_rect, width, height)
        crop = image[
            image_rect.y:image_rect.y + image_rect.height,
            image_rect.x:image_rect.x + image_rect.width,
        ].copy()
        screen_rect = WindowRect(
            left=window_rect.left + image_rect.x,
            top=window_rect.top + image_rect.y,
            width=image_rect.width,
            height=image_rect.height,
        )
        zones[name] = ZoneCapture(
            name=name,
            relative_rect=rel_rect,
            image_rect=image_rect,
            screen_rect=screen_rect,
            crop=crop,
        )

    return PerceptionFrame(
        window_rect=window_rect,
        image_shape=image.shape,
        hero_seat_name=HERO_SEAT_NAME,
        geometry_warning=geometry_warning,
        zones=zones,
    )
