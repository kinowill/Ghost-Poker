# Ghost-Poker

Agent IA pour poker en ligne. Perception hybride (DOM + vision), décision
hybride (solver GTO + LLM meta), contrôle souris.

**Statut** : en cours de bootstrap (J0). Voir [`MASTER.md`](MASTER.md) pour le cadrage complet et [`ROADMAP.md`](ROADMAP.md) pour les jalons.

## Installation

Prérequis : Windows, [`uv`](https://github.com/astral-sh/uv) installé.

```bash
uv sync
cp .env.example .env   # puis remplir les clés API
uv run python scripts/smoke_test.py
```

## Structure

```
src/ghost_poker/
  perception/   # capture écran + OCR + CV + DOM
  brain/        # solver + LLM meta
  control/      # souris/clavier humains
  orchestrator/ # boucle principale
  utils/        # logging, config
```

## Documents clés

- [`MASTER.md`](MASTER.md) — document maître (but, stack, architecture, état courant).
- [`ROADMAP.md`](ROADMAP.md) — jalons ordonnés J0 → J6 (A1) puis J7+ (A2).
- [`JOURNAL.md`](JOURNAL.md) — journal des validations réelles.
