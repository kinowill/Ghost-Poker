# Ghost-Poker — Journal de validation

## 2026-04-23 — J1.4 bis : watcher validé sur plusieurs mains

- **État** : repo modifié + validation réelle supplémentaire effectuée sur la stabilité partielle du watcher.
- **Ce qui a été fait** :
  - L'utilisateur a laissé tourner `uv run python scripts/watch_table_state.py --interval 0.75` sur PokerTH.
  - Observation continue sur plusieurs mains sans regénérer d'artefacts lourds.
- **Ce qui a été observé** :
  - La lecture a suivi une main complète de `Preflop` à `Flop` puis `Turn` sur `game_number=1`, `hand_number=1`.
  - Le watcher a ensuite observé des changements de `hand_number` et de `game_number` : `hand_number=2`, `hand_number=3`, puis `game_number=2`.
  - Les transitions utiles sont cohérentes :
    - `Preflop` : `pot_total=0`, `pot_bets=110`, `Raise/F3/$40`, `Call/F2/$20`, `Fold/F1`
    - `Flop` : `pot_total=400`, `pot_bets=0`, `Bet/F3/$20`, `Check/F2`
    - `Turn` : `pot_total=600`, puis `pot_bets=200`, puis `pot_bets=760`
  - Le héros reste correctement identifié sur plusieurs états valides (`Human Player`) et son stack suit la main (`5000` → `4960` → `4940` → `4900`).
  - Des frames OCR manifestement polluées ont aussi été observées (`hero_name` lisant du texte hors table, champs `null` en rafale) : le watcher va maintenant ignorer ces snapshots impossibles au lieu de les émettre.
  - Sur le lancement utilisateur standard, Paddle a téléchargé ses modèles dans `C:\Users\ArtLi\.paddlex\...` ; la lecture fonctionne, mais les caches ne sont pas encore totalement forcés dans le projet.
- **Ce qui reste à vérifier** :
  - Confirmer que le filtrage du watcher supprime bien le bruit sans masquer de vrais changements de main.
  - Stabiliser ensuite la lecture des cartes et décider si PokerTH mérite une zone `journal_log`.
- **Commit(s) liés** : aucun pour l'instant, travail local non commité.

---

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

## 2026-04-23 — J1.4 : zone `table_meta` + première lecture OCR partielle

- **État** : repo modifié + validation réelle partielle effectuée sur la lecture OCR J1.
- **Ce qui a été fait** :
  - Recalibration du layout PokerTH pour ajouter la zone `table_meta` (`Preflop / Game: X / Hand: Y`) dans `data/config/pokerth_layout.json`.
  - Ajout d'un moteur OCR local (`src/ghost_poker/perception/ocr.py`) et d'une première lecture structurée `TableState` (`src/ghost_poker/perception/table_state.py`), branchée dans `scripts/debug_perception.py`.
  - Durcissement du parsing OCR pour privilégier les vrais noms de sièges (`Player X`, `Human Player`) et les stacks monétaires, au lieu de confondre noms/actions/blinds.
  - Correction de la capture : `capture_pokerth()` remet maintenant PokerTH au premier plan avant screenshot pour éviter qu'une fenêtre Codex/terminal masque le pot ou le siège héros.
- **Ce qui a été observé** :
  - Un premier run OCR a été pollué par la fenêtre Codex superposée à PokerTH ; le problème a été diagnostiqué visuellement dans `data/captures/perception_debug/20260423-140610/window.png`.
  - Après correction de la capture, run réel OK dans `data/captures/perception_debug/20260423-140757/` : `geometry_warning=null`, `table_meta.street=Preflop`, `game_number=1`, `hand_number=1`, `pot.total=0`, `pot.bets=110`.
  - Les sièges remontent correctement sur cette main testée : `seat_1..seat_9 = Player 1..9`, `seat_10 = Human Player`, avec stacks cohérents (`5000`, `4990`, `4980`, etc.).
  - Le bug de hotkeys venait du parseur, pas de l'OCR : l'association par ordre de lecture produisait de faux couples (`F4` collé à `Raise`). Correction appliquée : association spatiale par position dans le crop, verrouillée par un test direct `tests/perception/test_table_state.py`.
  - Run réel de contrôle OK dans `data/captures/perception_debug/20260423-150522/` : actions relues correctement sur cette main (`All-In/F4`, presets `33/50/100`, `Raise/F3/$40`, `Call/F2/$20`, `Fold/F1`).
  - `scripts/watch_table_state.py` a été ajouté puis validé en réel sur PokerTH avec `--max-events 1`, pour surveiller un état compact sans générer d'artefacts lourds à chaque lecture.
  - Les cartes héros/board ne sont pas encore interprétées, volontairement, car l'OCR n'est pas la bonne méthode pour elles.
- **Ce qui reste à vérifier** :
  - Confirmer la stabilité de cette lecture sur plusieurs mains consécutives, pas sur un seul instantané.
  - Décider si le bloc `Journal` PokerTH doit devenir une zone optionnelle `journal_log` pour reconstruire l'historique d'action.
  - Identifier si PokerTH expose aussi des boutons de pré-action et/ou un signal temporel utile, en vue des futures rooms à temps limité.
  - Implémenter la lecture des cartes (template matching ou autre méthode dédiée), distincte de l'OCR.
- **Commit(s) liés** : aucun pour l'instant, travail local non commité.

---

## 2026-04-23 — Décision produit : budget temps humain + auto-actions à prévoir

- **État** : vérité projet mise à jour, pas de validation runtime nouvelle.
- **Ce qui a été fait** :
  - Contrainte explicitée par l'utilisateur : sur les interfaces avec temps limité, le bot ne devra pas seulement choisir une action correcte, mais aussi gérer un temps de réaction plausible et l'usage éventuel d'auto-actions (`check`, `call`, etc.).
  - La roadmap J1/J4/J5 et le document maître ont été alignés pour porter cette contrainte dès maintenant.
- **Ce qui a été observé** :
  - Cette contrainte impacte au moins trois briques futures : perception (timer + pré-actions si présentes), décision (politique temporelle par type de spot) et contrôle (garde-fou anti-timeout).
- **Ce qui reste à vérifier** :
  - Si PokerTH expose des éléments visuels suffisamment stables pour servir de terrain d'essai sur ce sujet.
  - À quel moment de A1 il est pertinent d'implémenter les auto-actions : dès que la perception les voit, ou après la boucle complète J5.
- **Commit(s) liés** : aucun pour l'instant, travail local non commité.

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
