"""Stabilisation de snapshots OCR avant emission/log."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


def snapshot_signature(snapshot: dict[str, Any]) -> str:
    """Retourne une signature stable pour comparer deux snapshots."""
    return json.dumps(snapshot, sort_keys=True, separators=(",", ":"))


@dataclass
class StableSnapshotEmitter:
    """Emet seulement un snapshot vu assez de fois de suite."""

    required_reads: int = 1
    _candidate_signature: str | None = None
    _candidate_reads: int = 0
    _last_emitted_signature: str | None = None

    def __post_init__(self) -> None:
        self.required_reads = max(1, self.required_reads)

    def should_emit(self, snapshot: dict[str, Any]) -> bool:
        signature = snapshot_signature(snapshot)

        if signature == self._candidate_signature:
            self._candidate_reads += 1
        else:
            self._candidate_signature = signature
            self._candidate_reads = 1

        if self._candidate_reads < self.required_reads:
            return False

        if signature == self._last_emitted_signature:
            return False

        self._last_emitted_signature = signature
        return True
