# Ghost-Poker — Journal de validation

> Trace des validations **réelles**. Une entrée = un événement observé,
> pas un événement prévu. Ordre antéchronologique (plus récent en haut).
>
> Format d'entrée :
>
> ```
> ## YYYY-MM-DD — <titre court>
> - État : repo modifié / prod alignée / validation réelle
> - Ce qui a été fait :
> - Ce qui a été observé :
> - Ce qui reste à vérifier :
> - Commit(s) liés :
> ```

---

## 2026-04-22 — J0 : environnement Python + outils prêts

- **État** : validation réelle côté environnement dev + outils externes.
- **Ce qui a été fait** :
  - `pyproject.toml` écrit (Python 3.12, deps de base + extras `dev`/`ocr`/`browser`).
  - Squelette `src/ghost_poker/` créé avec sous-modules.
  - `scripts/smoke_test.py` + `scripts/validate_j0.py` écrits.
  - `uv sync` : Python 3.12 + 37 paquets installés, `ghost_poker` en editable.
  - PokerTH 2.0.6 installé via `winget install PokerTH.PokerTH`.
  - Clé Mistral créée + collée dans `.env` local (gitignored).
- **Ce qui a été observé** :
  - Smoke test 10/10 imports OK.
  - Validation J0 : Mistral API répond (accès mistral-medium-latest entre autres), capture écran OK (1920×1080) → `data/captures/j0_validation.png`.
  - PokerTH installé, pas encore lancé visuellement (à confirmer par l'utilisateur).
  - Note technique : `mistralai 2.4.1` expose `Mistral` via `mistralai.client.sdk.Mistral` (pas `from mistralai import Mistral`). Import à retenir pour la suite.
- **Ce qui reste à vérifier pour clôturer J0 à 100 %** :
  - Utilisateur lance PokerTH une fois → confirme qu'une table s'affiche et qu'il peut démarrer une partie IA locale.
- **Commit(s) liés** : à créer maintenant.

---

## 2026-04-22 — Ouverture du projet + premier push

- **État** : repo modifié + distant aligné. Pas de code runtime à valider.
- **Ce qui a été fait** :
  - Cadrage projet : cibles A1 (PokerTH play money) puis A2 (rooms en ligne argent réel).
  - Stack figée (Python, `uv`, OCR + CV, solver maison, Mistral API free tier).
  - Création `MASTER.md`, `ROADMAP.md`, `JOURNAL.md`, `.gitignore`, `.env.example`.
  - `git init` + premier commit + remote `kinowill/Ghost-Poker` + push initial sur `main`.
- **Ce qui a été observé** :
  - Push OK, commit `c4f40d3` visible sur https://github.com/kinowill/Ghost-Poker.
  - 5 fichiers versionnés. `.claude/settings.local.json` exclu du repo.
- **Ce qui reste à vérifier** : J0 bootstrap complet (Python 3.12, uv, deps, PokerTH, clé Mistral).
- **Commit(s) liés** : `c4f40d3` (docs: bootstrap projet Ghost-Poker).
