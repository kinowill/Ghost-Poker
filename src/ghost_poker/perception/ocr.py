"""OCR utilitaire pour les zones PokerTH."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def ensure_ocr_env() -> None:
    """Force les caches Paddle dans le projet pour rester reproductible."""
    cache_root = _project_root() / "data" / "cache"
    paddle_home = cache_root / "paddle"
    paddlex_home = cache_root / "paddlex"
    paddle_home.mkdir(parents=True, exist_ok=True)
    paddlex_home.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("PADDLE_HOME", str(paddle_home))
    os.environ.setdefault("PADDLEX_HOME", str(paddlex_home))
    os.environ.setdefault("XDG_CACHE_HOME", str(cache_root))
    os.environ.setdefault("HOME", str(cache_root))
    os.environ.setdefault("USERPROFILE", str(cache_root))


@dataclass(frozen=True)
class OCRLine:
    """Ligne OCR reconnue dans une zone."""

    text: str
    score: float
    left: int
    top: int
    width: int
    height: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "score": round(self.score, 4),
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }


@lru_cache(maxsize=1)
def get_ocr_engine() -> Any:
    """Construit une instance OCR réutilisable pour toutes les lectures."""
    ensure_ocr_env()

    from paddleocr import PaddleOCR

    return PaddleOCR(
        lang="en",
        device="cpu",
        enable_mkldnn=False,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )


def _box_to_rect(box: Any) -> tuple[int, int, int, int]:
    points = np.asarray(box, dtype=np.int32)
    if points.ndim == 1 and points.size == 4:
        left, top, right, bottom = map(int, points.tolist())
        return left, top, max(1, right - left), max(1, bottom - top)
    xs = points[:, 0]
    ys = points[:, 1]
    left = int(xs.min())
    top = int(ys.min())
    width = max(1, int(xs.max() - left))
    height = max(1, int(ys.max() - top))
    return left, top, width, height


def read_ocr_lines(image: np.ndarray) -> list[OCRLine]:
    """Retourne les lignes OCR reconnues, triées de haut en bas."""
    engine = get_ocr_engine()
    result = engine.predict(image)
    if not result:
        return []

    page = result[0]
    texts = page.get("rec_texts", [])
    scores = page.get("rec_scores", [])
    boxes = page.get("rec_boxes", [])

    lines: list[OCRLine] = []
    for text, score, box in zip(texts, scores, boxes, strict=False):
        if not str(text).strip():
            continue
        left, top, width, height = _box_to_rect(box)
        lines.append(
            OCRLine(
                text=str(text).strip(),
                score=float(score),
                left=left,
                top=top,
                width=width,
                height=height,
            )
        )

    return sorted(lines, key=lambda line: (line.top, line.left))
