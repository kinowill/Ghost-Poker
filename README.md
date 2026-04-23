# Ghost-Poker

Agent IA de poker. Perception hybride (DOM + vision), décision hybride
(solver GTO + couche meta LLM interchangeable) et exécution pilotée par
mode `assist` ou `autonomous`.

**Statut** : J1 en cours (perception OCR partielle déjà branchée sur PokerTH).
Voir [`MASTER.md`](MASTER.md) pour le cadrage complet et [`ROADMAP.md`](ROADMAP.md)
pour les jalons.

## Installation

Prérequis : Windows, [`uv`](https://github.com/astral-sh/uv) installé.

```bash
uv sync
cp .env.example .env   # optionnel : seulement si un backend API est utilisé
uv run python scripts/smoke_test.py
```

## Structure

```
src/ghost_poker/
  perception/   # capture écran + OCR + CV + DOM
  brain/        # solver + couche meta LLM interchangeable (API ou local)
  control/      # pilotage souris/clavier en mode assistance ou 100 % autonome
  orchestrator/ # boucle principale
  utils/        # logging, config
```

## Principes produit

- Le backend meta ne doit pas être figé à Mistral : toute clé API compatible
  ou tout modèle local exploitable devra pouvoir être branché proprement.
- Le contrôle ne doit pas être limité à une simple assistance : le produit doit
  pouvoir fonctionner soit en aide à la décision, soit en prise en main 100 % IA.

## Documents clés

- [`MASTER.md`](MASTER.md) — document maître (but, stack, architecture, état courant).
- [`ROADMAP.md`](ROADMAP.md) — jalons ordonnés J0 → J6 (A1) puis J7+ (A2).
- [`JOURNAL.md`](JOURNAL.md) — journal des validations réelles.
