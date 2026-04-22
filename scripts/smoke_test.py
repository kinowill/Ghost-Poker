"""Smoke test J0 : vérifie que toutes les deps de base importent.

Usage :
    uv run python scripts/smoke_test.py
"""

import sys


def main() -> int:
    errors = []

    checks = [
        ("mss", "mss"),
        ("opencv-python", "cv2"),
        ("numpy", "numpy"),
        ("pyautogui", "pyautogui"),
        ("treys", "treys"),
        ("loguru", "loguru"),
        ("mistralai", "mistralai"),
        ("python-dotenv", "dotenv"),
        ("pydantic", "pydantic"),
        ("ghost_poker", "ghost_poker"),
    ]

    for pkg_name, import_name in checks:
        try:
            mod = __import__(import_name)
            version = getattr(mod, "__version__", "?")
            print(f"  OK  {pkg_name:20s} {version}")
        except Exception as e:  # noqa: BLE001
            errors.append((pkg_name, str(e)))
            print(f"  KO  {pkg_name:20s} {e}")

    print()
    if errors:
        print(f"FAIL : {len(errors)} import(s) en erreur.")
        return 1
    print("OK : toutes les deps importent correctement.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
