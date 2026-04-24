"""Affiche le profil runtime derive de la configuration Ghost-Poker.

Usage:
    uv run python scripts/show_runtime_profile.py
"""

from __future__ import annotations

import json
import sys

from ghost_poker.orchestrator import build_runtime_profile
from ghost_poker.utils import load_runtime_config


def main() -> int:
    runtime_config = load_runtime_config()
    profile = build_runtime_profile(runtime_config)
    print(json.dumps(profile.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
