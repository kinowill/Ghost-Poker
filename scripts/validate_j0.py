"""Validation J0 : clé Mistral fonctionnelle + capture écran OK.

Usage :
    uv run python scripts/validate_j0.py
"""

import os
import sys
from pathlib import Path

import mss
from dotenv import load_dotenv
from loguru import logger


def check_mistral() -> bool:
    load_dotenv()
    key = os.environ.get("MISTRAL_API_KEY", "").strip()
    if not key:
        logger.error("MISTRAL_API_KEY absent de .env")
        return False

    try:
        from mistralai.client.sdk import Mistral
    except ImportError as e:
        logger.error(f"mistralai non importable : {e}")
        return False

    try:
        client = Mistral(api_key=key)
        # Appel minimal : lister les modèles (gratuit, pas de tokens consommés)
        models = client.models.list()
        model_ids = [m.id for m in models.data][:5]
        logger.info(f"Mistral OK — premiers modèles accessibles : {model_ids}")
        return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"Appel Mistral échoué : {e}")
        return False


def check_screen_capture() -> bool:
    out_dir = Path("data/captures")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "j0_validation.png"

    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # écran principal
            shot = sct.grab(monitor)
            mss.tools.to_png(shot.rgb, shot.size, output=str(out_path))
        logger.info(f"Capture écran OK ({shot.size}) → {out_path}")
        return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"Capture échouée : {e}")
        return False


def main() -> int:
    logger.info("=== Validation J0 ===")

    ok_mistral = check_mistral()
    ok_capture = check_screen_capture()

    print()
    logger.info(f"Mistral API  : {'OK' if ok_mistral else 'KO'}")
    logger.info(f"Screen capture : {'OK' if ok_capture else 'KO'}")

    if ok_mistral and ok_capture:
        logger.success("J0 validé techniquement.")
        return 0
    logger.error("J0 non validé — voir erreurs ci-dessus.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
