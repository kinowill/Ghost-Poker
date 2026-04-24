# Ghost-Poker — Roadmap

> Liste ordonnée des jalons. Chaque jalon est **validable seul**
> (état "validation réelle" au sens du MASTER, section 8).
> Avancer J+1 sans J validé = interdit.

**Légende** : ⏳ à faire · 🔄 en cours · ✅ validé · ⛔ bloqué

---

## Phase A1 — Bot joue en play money offline (PokerTH)

### J0 — Bootstrap ✅

**But** : environnement de dev prêt, pas une ligne de logique métier.

- Installer Python 3.12 + `uv` (si absent).
- `uv init` + `pyproject.toml` avec deps de base (`mss`, `opencv-python`, `paddleocr`, `pyautogui`, `treys`, `loguru`, `pytest`, `mistralai`, `python-dotenv`).
- Créer `src/ghost_poker/` + sous-modules (vides avec `__init__.py`).
- `git init` + premier commit + ajout du remote `kinowill/Ghost-Poker` + push.
- Installer **PokerTH** (client offline play money, banc de test) et vérifier qu'il démarre.
- Créer compte Mistral (free tier) + clé API dans `.env` local.

**Critère de validation** : `uv run python -c "import mss, cv2, paddleocr, pyautogui, treys; print('OK')"` passe. PokerTH s'ouvre. Repo pushé.

---

### J1 — Perception : capture + OCR → état table JSON 🔄

**But** : depuis une fenêtre PokerTH ouverte, produire un dict Python décrivant
l'état exact de la table (cartes, stacks, pot, blinds, actions possibles, joueur à parler).

- Calibrer les zones d'intérêt sur capture PokerTH (layout figé).
- Template matching cartes (`data/templates/cards/`).
- OCR stacks / pot / blinds via PaddleOCR.
- Détection joueur actif (bordure / couleur).
- Prévoir dès la perception les éléments utiles au budget temps et aux pré-actions quand ils existent (timer, boutons auto-check/auto-call/auto-fold, etc.).
- Sortie normalisée : `TableState` (dataclass).
- Script `scripts/debug_perception.py` qui affiche l'état lu en temps réel.

**Critère de validation** : 20 mains consécutives, état JSON correct à 100 % sur toutes les rues. Diffs visibles dans `JOURNAL.md`.

**État intermédiaire au 2026-04-23** : capture de référence + calibration du layout validées visuellement en plein écran. La capture vise la zone client PokerTH et le layout versionné contient maintenant une taille de référence (`1920×1032`) ainsi qu'une zone `table_meta`. `scripts/debug_perception.py` est validé en réel sur table ouverte et produit maintenant un premier `TableState` partiel : `table_meta`, `pot`, `actions` et `seat_1..seat_10` remontent sur la main testée. Le mapping des actions a été corrigé par position réelle dans le crop (hotkeys + montants), et `scripts/watch_table_state.py` permet maintenant de surveiller l'état compact sur plusieurs mains tout en journalisant automatiquement chaque changement plausible dans `data/logs/table_state/<timestamp>/events.jsonl`. Les cartes (`hero_cards`, `board`) ne sont pas encore lues et la robustesse doit être confirmée sur plusieurs mains.

**Complément de validation** : le watcher a déjà suivi une même main de `Preflop` à `Flop` puis `Turn`, puis plusieurs changements de `hand_number` et `game_number`. Le prochain vrai critère n'est plus "voit-on des changements ?", mais "les voit-on sans bruit parasite sur une séquence plus longue ?".

---

### J2 — Solver préflop ⏳

**But** : décisions GTO-correctes préflop en fonction position + action précédente.

- Intégrer ranges GTO (`data/ranges/preflop/`) — sources ouvertes (GTOWizard free, PokerSnowie chart public).
- Moteur qui, étant donnés `(position, action_in_front, stack_bb)`, sort `{fold, call, raise, sizing}` avec mix optionnel.
- Tests unitaires sur 50 spots classiques.

**Critère de validation** : 50/50 spots passent. Décision produite en < 10 ms.

---

### J3 — Solver postflop v1 (Monte Carlo) ⏳

**But** : décisions correctes postflop via équité Monte Carlo + ranges adverses simplifiées.

- Range villain inférée depuis action préflop (ouverture/3bet → range typique).
- `treys` pour eval équité par MC (10k itérations).
- Heuristiques pot odds / implied odds / SPR.
- Décision : fold / check / call / bet / raise + sizing (1/3 pot, 1/2, 2/3, pot).

**Critère de validation** : 100 spots postflop manuels, ≥ 85 % d'accord avec un solver de référence (ou avis joueur expérimenté).

---

### J4 — Contrôle interface assisté/autonome ⏳

**But** : exécuter `fold/call/raise/montant` dans PokerTH via souris/clavier, avec un mode `assist` et un mode `autonomous`, sans gestes robotiques.

**État intermédiaire au 2026-04-24** : le contrat runtime existe déjà (`assist|autonomous`, `dry_run|armed`), `watch_action_plan.py` est validé en réel dans les deux modes, et un premier exécuteur OS garde-fou sait maintenant envoyer uniquement des hotkeys simples en mode `armed`. Les sliders restent volontairement bloqués à ce stade. Le panneau visible local (`control_panel.py` + état JSON partagé) est maintenant validé en réel pour `ARM NEXT`.

**Complément de validation** : le chemin `autonomous + dry_run` est maintenant validé en vrai sur un spot `Call/F2`, et l'armement explicite `--arm-key f10` a lui aussi été validé en vrai : sur plusieurs vrais spots `Call`, aucun envoi n'est parti sans maintien de `F10`. `scripts/debug_key_state.py` a ensuite confirmé que Windows voit bien `F10`, `right_shift` et `ctrl` sur ce poste, puis `scripts/debug_arm_window.py` a confirmé que la fenêtre armée elle-même voit bien `F10` quand elle est maintenue correctement et que `F12` garde bien la priorité. En revanche, `right_shift` puis `F10` ont tous deux échoué sur de vrais spots PokerTH malgré `99` puis `100` échantillons. Le panneau visible local a ensuite été validé en réel : `ARM NEXT` autorise bien une action unique, puis repasse automatiquement à `paused`. Le prochain critère utile est maintenant de valider explicitement `PAUSE` sur un spot actionnable, puis `ARM HOLD` sur plusieurs spots successifs.

**Point méthodologique confirmé** : tester le kill switch "quand `Call` apparaît" est insuffisant si la room autorise des pré-actions. Le prochain vrai critère doit donc passer par un armement explicite juste avant envoi, pas par la simple visibilité du bouton. Le script supporte maintenant cet armement via `--arm-key`.

- Courbes Bézier 2D (départ → cible) avec points de contrôle jittered.
- Vitesse variable (ease-in/out).
- Micro-pauses aléatoires avant clic.
- Typage des montants (clavier + backspace occasionnel).
- Sélecteur de mode produit : aide à la décision seule ou prise en main 100 % IA.
- Budget temps et garde-fou anti-timeout : le bot doit toujours agir avant la limite, même si la réflexion "humaine" simulée varie.
- Support des auto-actions quand l'interface les propose (`auto-check`, `call any`, etc.), sans les rendre obligatoires.
- Test : 100 clics, 0 raté, distribution des trajectoires visuellement humaine.

**Critère de validation** : 10 mains jouées via le module de contrôle dans chacun des deux modes, 0 erreur d'action.

---

### J5 — Boucle complète ⏳

**But** : Perception → Cerveau (solver seul) → Contrôle. Bot joue seul une session.

- Orchestrateur : boucle d'état, anti-double-action, gestion des transitions de rue.
- Solver seul (pas encore de LLM meta).
- Politique temporelle : chaque décision doit sortir avec une fenêtre de réaction plausible (spot simple, spot de value, bluff, tank court, urgence proche timeout).
- Politique de pré-action : si l'interface permet une auto-action cohérente et utile, le bot doit pouvoir la sélectionner avant son tour.
- Kill switch clavier (ex. `F12` → stop immédiat).
- Logs structurés `loguru` : chaque décision + état + sizing + raisonnement.

**Critère de validation** : **1 session complète de 100 mains** sur PokerTH sans intervention humaine, sans crash, décisions tracées dans `JOURNAL.md`.

---

### J6 — LLM meta backend-agnostic pour ajustements exploitatifs ⏳

**But** : couche "lecture des adversaires" par-dessus le solver.

- À la fin de chaque main, stats adversaires mises à jour (VPIP, PFR, agression, showdowns observés).
- Toutes les N mains (ou sur spot critique), appel du backend meta configuré avec contexte condensé → retourne des overrides exploitatifs (ex : "HJ fold trop, 3bet light depuis BTN").
- Solver applique les overrides comme biais sur décisions marginales.
- Adaptateur de provider pour accepter aussi bien une clé API qu'un backend local.
- Cache + rate-limit pour tenir sur free tier quand on utilise un provider distant.

**Critère de validation** : A/B session sans LLM vs avec backend meta sur 500 mains, meta ≥ solver pur sur winrate bb/100 (ou au pire égal sans régression).

---

## Phase A2 — Passage en ligne argent réel (R&D, plusieurs jalons)

> **Important** : A2 est un chantier R&D à part entière, pas un toggle.
> Les jalons A2 ne s'ouvrent qu'une fois **tout A1 validé**.

### J7 — Portage perception sur room cible ⏳
### J8 — Furtivité navigateur ⏳
### J9 — Furtivité comportementale ⏳
### J10 — Validation argent fictif en ligne ⏳
### J11 — Décision argent réel : go / no-go ⏳

Détails de A2 à écrire quand A1 sera validé. Il est volontairement prématuré
de les spécifier finement tant que A1 n'a pas révélé ses points durs.

---

## Prochaine action

**J1 – Perception.** Utiliser `watch_table_state.py` avec son auto-log JSONL pour valider la stabilité sur plusieurs mains (pot / actions / sièges / `table_meta`), puis décider si PokerTH mérite des zones optionnelles `journal_log` et `timer/pre-actions` pour préparer le budget temps et les actions automatiques.
