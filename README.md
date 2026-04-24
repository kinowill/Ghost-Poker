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

## Configuration runtime

- `GHOST_POKER_CONTROL_MODE=assist|autonomous`
- `GHOST_POKER_EXECUTION_SAFETY=dry_run|armed`
- `GHOST_POKER_CONTROL_GATE_MODE=disabled|panel`
- `GHOST_POKER_CONTROL_STATE_PATH=data/runtime/control_panel_state.json`
- `GHOST_POKER_META_BACKEND=disabled|mistral|groq|openai_compatible|ollama|local`
- `GHOST_POKER_META_MODEL=...`
- `GHOST_POKER_META_BASE_URL=...`
- `GHOST_POKER_META_API_KEY=...`

Commande de diagnostic :

```bash
uv run python scripts/show_runtime_profile.py
```

Preview live du contrat d'action :

```bash
uv run python scripts/watch_action_plan.py --decision auto
```

Panneau local visible always-on-top :

```bash
uv run python scripts/control_panel.py
```

Si `control_mode=autonomous`, l'exécution reste simulée tant que
`GHOST_POKER_EXECUTION_SAFETY=dry_run`. Le mode `armed` n'exécute pour l'instant
que les actions hotkey simples (`F1`..`F4`) et bloque volontairement les sliders.
Si `GHOST_POKER_CONTROL_GATE_MODE=panel`, l'exécution dépend aussi du panneau local :
- `ARM NEXT` : autorise une seule action, puis revient à `PAUSE`
- `ARM HOLD` : autorise les actions tant que le panneau reste armé
- `PAUSE` : bloque les actions
- `STOP` : bloque les actions et marque un arrêt explicite
`watch_action_plan.py` écrit aussi automatiquement ses événements dans
`data/logs/action_plan/<timestamp>/events.jsonl`, et accepte `--armed-delay-ms`
pour laisser le temps d'appuyer sur le kill switch avant un envoi réel.
Il accepte aussi `--arm-key` pour exiger un armement explicite avant un envoi réel.
Les modifieurs comme `right_shift`, `ctrl` ou `space` sont souvent plus fiables que `f10` sur les claviers laptop.
Si un doute subsiste sur la touche réellement vue par Windows, utiliser :

```bash
uv run python scripts/debug_key_state.py
```

Si le doute porte spécifiquement sur la fenêtre armée elle-même, sans dépendre
de PokerTH ni d'un spot actionnable :

```bash
uv run python scripts/debug_arm_window.py --delay-ms 5000 --arm-key f10
```

## Documents clés

- [`MASTER.md`](MASTER.md) — document maître (but, stack, architecture, état courant).
- [`ROADMAP.md`](ROADMAP.md) — jalons ordonnés J0 → J6 (A1) puis J7+ (A2).
- [`JOURNAL.md`](JOURNAL.md) — journal des validations réelles.
