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

## 2026-04-22 — J0 : environnement Python prêt

- **État** : validation réelle côté environnement dev.
- **Ce qui a été fait** :
  - `pyproject.toml` écrit (Python 3.12, deps de base + extras `dev`/`ocr`/`browser`).
  - Squelette `src/ghost_poker/` créé avec sous-modules (`perception`, `brain`, `control`, `orchestrator`, `utils`).
  - `scripts/smoke_test.py` pour vérifier que toutes les deps de base importent.
  - `README.md` minimal pointant sur MASTER / ROADMAP / JOURNAL.
  - `uv sync` : Python 3.12 téléchargé, 37 paquets installés, `ghost_poker` installé en editable.
- **Ce qui a été observé** :
  - `uv run python scripts/smoke_test.py` → 10/10 OK (mss, cv2, numpy, pyautogui, treys, loguru, mistralai, dotenv, pydantic, ghost_poker).
- **Ce qui reste à vérifier pour clôturer J0** :
  - Installation PokerTH (manuel, utilisateur).
  - Création clé API Mistral dans `.env` (manuel, utilisateur).
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
