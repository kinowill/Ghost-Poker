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

## 2026-04-23 — J1.3 : extraction des zones + debug_perception

- **État** : repo modifié + validation réelle effectuée pour l'extraction géométrique J1.3.
- **Ce qui a été fait** :
  - Ajout d'un module `src/ghost_poker/perception/regions.py` pour extraire les zones calibrées depuis une capture PokerTH.
  - Ajout de `scripts/debug_perception.py` pour capturer la fenêtre, sauvegarder chaque crop et écrire un `summary.json`.
  - Refactor léger : la vérification de géométrie vit maintenant dans `Layout`, réutilisée par `preview_layout.py`.
- **Ce qui a été observé** :
  - Validation syntaxique OK sur les fichiers Python modifiés.
  - Exécution réelle OK sur PokerTH ouvert : `window_rect=1920×1032`, `geometry_warning=null`, artefacts générés dans `data/captures/perception_debug/20260423-130829/`.
  - Les crops ouverts et vérifiés (`hero_cards`, `board`, `actions`, `seat_10`) sont cohérents avec la table affichée.
- **Ce qui reste à vérifier** :
  - La lecture réelle du contenu (cartes, pot, stacks, actions) n'est pas encore implémentée.
  - La stack OCR est maintenant installée dans l'environnement projet (`paddleocr 3.5.0`, `paddle 3.3.1`) et les imports ont été revérifiés.
  - La prochaine avancée consiste à brancher cette stack dans une première lecture réelle (pot / board / actions / sièges).
- **Commit(s) liés** : aucun pour l'instant, travail local non commité.

---

## 2026-04-23 — J1.2 : calibration du layout PokerTH

- **État** : repo modifié + validation réelle effectuée pour J1.2 (layout calibré et aperçu confirmé).
- **Ce qui a été fait** :
  - `scripts/calibrate_layout.py` relancé après passage PokerTH en plein écran/maximisé.
  - Les 14 zones demandées ont été retracées puis sauvegardées dans `data/config/pokerth_layout.json`.
  - Le script de calibration a été ajusté pour afficher les consignes dans une fenêtre séparée, sans masquer le haut de table.
  - `scripts/preview_layout.py` relancé sur cette géométrie finale.
- **Ce qui a été observé** :
  - Sauvegarde confirmée : `data/config/pokerth_layout.json` contient 14 zones et des métadonnées de référence (`1920×1032`, `hero_seat_name=seat_10`).
  - Le mapping réel de ce layout est `seat_10` = `Human Player` ; l'hypothèse précédente sur `seat_5` était fausse.
  - Le layout est relatif à la fenêtre PokerTH courante, pas au plein écran.
  - Après resize de la fenêtre, les boxes se décalent : PokerTH ne garde pas une géométrie strictement homothétique.
  - Correction locale ajoutée : capture sur zone client + avertissement quand la taille courante ne correspond plus à la calibration.
  - Validation utilisateur : aperçu visuel bon en plein écran/maximisé, zones jugées correctement alignées.
- **Ce qui reste à vérifier** :
  - La lecture réelle des sous-zones (cartes, pot, stacks, actions) n'est pas encore implémentée ni validée.
  - Ne plus redimensionner PokerTH après cette calibration ; en cas de resize, recalibrer.
- **Commit(s) liés** : aucun pour l'instant, travail local non commité.

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
  - ✅ Utilisateur a lancé PokerTH, table fonctionnelle, partie IA locale jouable.
- **Commit(s) liés** : `506aab4`, `aea4f80`. README affiné par utilisateur (`8f18380`).

**→ J0 clos. Ouverture J1 : perception.**

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
