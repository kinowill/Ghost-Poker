# Ghost-Poker — Document maître

> Référence opérative du projet. Lu seul, ce fichier doit donner
> une image exacte de Ghost-Poker à l'instant T.
> Mis à jour à chaque session qui modifie la vérité du projet.

**Repo distant** : https://github.com/kinowill/Ghost-Poker (actif, branche `main` poussée)
**Dossier local** : `C:\PROJETS\POKER\` (à renommer éventuellement en `Ghost-Poker` si souhaité)

---

## 1. Nom et but

**Ghost-Poker** — agent IA qui joue au poker en ligne de manière
ultra optimisée, en percevant la table (DOM + vision) et en pilotant
l'interface soit en assistance à la décision, soit en autonomie complète.

**Cible finale (A2)** : jouer en argent réel sur rooms en ligne (Winamax, GG,
PokerStars, PMU, etc.), furtivement, décisions GTO-correctes ajustées
exploitativement.

**Cible v1 (A1)** : même agent, mais sur **client offline play money
(PokerTH)**, pour valider toutes les briques sans risque juridique ni
de bankroll. Les briques sont identiques, seule la couche furtivité
change au passage A1 → A2.

---

## 2. Zones sensibles (à ne jamais oublier)

- **ToS rooms en ligne** : toute RTA / bot est explicitement interdite.
  Détection active en 2026 : empreinte souris, timings, focus fenêtre,
  hooks, patterns de décision. **Sanction type en argent réel : saisie des
  fonds + ban définitif.** Pas un détail.
- **Cadre légal FR (ANJ)** : assistance IA sur argent réel en ligne =
  fraude au sens du règlement.
- **Conséquence opératoire** : v1 A1 reste 100 % safe (offline, play money,
  client libre). La phase A2 doit être traitée comme un **chantier R&D
  à part entière**, pas comme un simple toggle.
- **Décision produit assumée** : le produit devra exposer deux modes
  explicites, `assist` (aide seulement) et `autonomous` (prise en main
  100 % IA). Ce choix ne doit pas être implicite ni codé en dur.

---

## 3. Stack technique

| Couche | Outil | Rôle |
|---|---|---|
| Langage | Python 3.12 | Tout le projet |
| Gestion pkgs | `uv` | Venv + deps rapide |
| Capture écran | `mss` | Screenshots 60 fps |
| Vision CV | `opencv-python` | Détection zones, template matching (cartes, boutons) |
| OCR | `paddleocr` | Lecture stacks, pot, noms, montants |
| VLM fallback | `moondream2` ou `qwen2.5-vl-3b` quantisé (Ollama) | État de table ambigu uniquement |
| DOM/réseau | `playwright` (mode passif) | Lecture client web quand DOM exploitable |
| Évaluateur mains | `treys` | Hand strength, équités |
| Solver | Moteur maison Python | Ranges préflop + Monte Carlo postflop v1, CFR-lite v2 |
| LLM meta | Backend interchangeable (API ou local) | Lecture villain, ajustements exploitatifs |
| Backend initial | `mistralai` SDK + Groq API | Point de départ pratique, pas dépendance figée |
| Contrôle OS | `pyautogui` + courbes Bézier maison + jitter temporel | Exécution assistée ou autonome, avec gestes non robotiques |
| Tests | `pytest` | Unitaires + intégration |
| Logs | `loguru` | Journal structuré |

**Hardware cible** (machine utilisateur) :
Ryzen 5 5600H, 16 Go RAM, RTX 3050 Laptop 4 Go VRAM, SSD 477 Go, Windows 11.
→ Tout le local (OCR, CV, petits VLM quantisés, solver) passe.
Gros LLM = API au départ, mais l'architecture doit rester compatible avec
des backends locaux si la machine ou la qualité le permettent.

---

## 4. Architecture

```
[Capture écran / DOM]  ──▶  [Perception]  ──▶  État table (JSON)
                                                      │
                                                      ▼
                                              [Cerveau]
                                                      │
                                           Solver (GTO) + LLM meta (exploit)
                                                      │
                                                      ▼
                                              Décision (fold/call/raise/montant)
                                                      │
                                                      ▼
                                  [Mode assist ou autonomous]
                                                      |
                                                      ▼
                                  [Contrôle souris/clavier autonome]
```

Boucle orchestrateur : poll perception → si état change → décider → agir → attendre.

---

## 5. Structure de fichiers

```
C:\PROJETS\POKER\
├── MASTER.md              # ce fichier
├── ROADMAP.md             # jalons ordonnés
├── JOURNAL.md             # trace des validations réelles
├── README.md              # (à créer plus tard)
├── pyproject.toml         # deps via uv
├── .gitignore
├── .env.example           # clés API (template, pas de secrets)
├── src/
│   └── ghost_poker/
│       ├── __init__.py
│       ├── perception/    # vision + DOM + OCR
│       ├── brain/         # solver + couche meta backend-agnostic
│       ├── control/       # exécution interface (assistée ou autonome)
│       ├── orchestrator/  # boucle principale
│       └── utils/         # logging, config
├── tests/
├── data/
│   ├── templates/         # images cartes/boutons pour template matching
│   └── ranges/            # ranges préflop GTO
└── scripts/               # outils ponctuels (calibration, capture, debug)
```

---

## 6. Sources de vérité

Dans l'ordre de priorité :

1. **MASTER.md** (ce fichier) — référence opérative.
2. **ROADMAP.md** — ce qui est fait, en cours, à faire.
3. **JOURNAL.md** — trace des validations réelles.
4. **Code source** (`src/`) et configuration réelle — vérité runtime.
   En cas de conflit avec une doc plus ancienne, **c'est le code qui gagne**.
5. **Repo distant** (https://github.com/kinowill/Ghost-Poker) — vérité partagée
   quand les commits locaux sont poussés sur `main`.

---

## 7. État courant (à maintenir à jour)

**Date** : 2026-04-24
**Phase** : J1 — Perception (capture + OCR → état table JSON).

**J0 clos ✅** (toutes cases cochées, PokerTH confirmé fonctionnel par l'utilisateur).

**J1.1 + J1.2 validés** : capture de référence réalisée, layout recalibré puis validé visuellement en plein écran. `data/config/pokerth_layout.json` contient maintenant 15 zones, dont `table_meta`, plus les métadonnées de référence.

**J1.3 validé en réel** : `scripts/debug_perception.py` capture bien la table PokerTH ouverte, découpe les 15 zones, sauvegarde les crops et écrit un résumé JSON sans alerte de géométrie.

**Première lecture OCR branchée, validation partielle** : `src/ghost_poker/perception/ocr.py` et `table_state.py` lisent maintenant une première version structurée de `table_meta`, `pot`, `actions` et des sièges. Validation réelle observée sur PokerTH : `street=Preflop`, `game=1`, `hand=1`, `pot.total=0`, `pot.bets=110`, `seat_1..seat_10` relus avec noms/stacks cohérents sur la main testée, et panneau d'action relu correctement (`All-In/F4`, presets `33/50/100`, `Raise/F3/$40`, `Call/F2/$20`, `Fold/F1`).

**Prochain pas immédiat** : valider en réel sur PokerTH le watcher stabilisé
(`--stable-reads`, 2 lectures identiques par défaut), qui journalise automatiquement
ses changements d'état en JSONL, puis traiter les éléments encore incomplets ou
non fiables (cartes hero/board, historique d'action détaillé, éventuelle zone
`journal_log` optionnelle pour PokerTH).

**Notes techniques à retenir** :
- `mistralai 2.4.1` : `from mistralai.client.sdk import Mistral` (pas le top-level).
- Résolution écran utilisateur : 1920×1080.
- PokerTH installé via winget (`PokerTH.PokerTH` 2.0.6).
- Le layout est calibré relativement à la fenêtre PokerTH, pas au plein écran.
- Mapping observé sur cette table : `seat_10` = `Human Player`, avec `hero_cards` et `actions` au bas de la fenêtre.
- La capture travaille maintenant sur la zone client PokerTH (sans bordures/barre de titre).
- La capture remet PokerTH au premier plan juste avant le screenshot pour éviter qu'une fenêtre terminal/éditeur ne pollue les crops.
- Limite actuelle : un resize de fenêtre apres calibration peut invalider les zones ; tant qu'on n'a pas d'ancrages visuels, il faut recalibrer a la taille voulue.
- Géométrie de référence actuellement validée : `1920×1032` (plein écran/maximisé PokerTH sur ce poste).
- J1.3 observé en réel sur ce poste : `window_rect=1920×1032`, `geometry_warning=null`, crops cohérents au moins pour `hero_cards`, `board`, `actions`, `seat_10`.
- Run OCR de référence actuel : `data/captures/perception_debug/20260423-140757/summary.json`.
- Validation compacte en continu disponible via `scripts/watch_table_state.py` ; run réel de référence : lecture compacte OK sur PokerTH (`Preflop`, `pot=0/110`, `Raise/Call/Fold` avec hotkeys).
- `scripts/watch_table_state.py` ouvre désormais un dossier horodaté sous `data/logs/table_state/` et y écrit automatiquement chaque changement d'état plausible dans `events.jsonl`, pour éviter tout copier-coller manuel.
- `scripts/watch_table_state.py` utilise maintenant une stabilisation locale des
  snapshots OCR (`--stable-reads`, défaut `2`) pour éviter d'émettre/logguer un
  bruit isolé. Validation automatisée OK, validation PokerTH réelle encore à faire.
- Le code porte maintenant un socle runtime explicite pour `GHOST_POKER_CONTROL_MODE=assist|autonomous` et pour un backend meta interchangeable (`disabled`, `mistral`, `groq`, `openai_compatible`, `ollama`, `local`) via `src/ghost_poker/utils/runtime_config.py`.
- Un point d'entrée de diagnostic existe maintenant : `scripts/show_runtime_profile.py` charge `.env`, construit le profil runtime dérivé (`assist|autonomous` + backend meta) et l'affiche en JSON.
- Le contrat d'action commence à être branché : `DecisionIntent` (côté cerveau) et `ActionPlan` (côté orchestrateur) changent déjà selon `assist|autonomous` et valident les actions visibles (`call`, `raise`, `all-in`, override slider) avant toute future exécution OS.
- Un preview live existe maintenant : `scripts/watch_action_plan.py` lit la vraie table PokerTH, choisit une décision heuristique simple ou forcée en CLI, puis affiche l'`ActionPlan` résultant en direct.
- Un garde-fou d'exécution existe maintenant : `GHOST_POKER_EXECUTION_SAFETY=dry_run|armed`. En `dry_run`, aucune action OS réelle n'est envoyée ; en `armed`, l'exécution est pour l'instant limitée aux hotkeys simples et bloquée si le kill switch Windows configuré est détecté.
- `watch_action_plan.py` journalise maintenant aussi ses événements dans `data/logs/action_plan/<timestamp>/events.jsonl`, accepte `--armed-delay-ms` pour laisser un délai avant un envoi réel en mode `armed`, et accepte `--arm-key` pour exiger un armement explicite avant tout envoi.
- La couche de détection clavier ne se limite plus aux touches `F1..F12` : elle accepte aussi des modifieurs (`shift`, `right_shift`, `ctrl`, `right_ctrl`, `alt`, `space`, etc.) et un script `scripts/debug_key_state.py` permet maintenant de voir quelles touches Windows détecte réellement sur ce poste.
- Validation réelle supplémentaire : `scripts/debug_key_state.py` a confirmé sur ce poste que Windows voit bien `F10`, `right_shift` et `ctrl`. Le problème observé sur `--arm-key f10` ne vient donc pas d'une touche globalement invisible pour Windows ; il faut maintenant instrumenter la fenêtre armée elle-même.
- Un script `scripts/debug_arm_window.py` existe maintenant pour tester la fenêtre armée seule, avec les mêmes compteurs (`arm_seen`, `arm_seen_samples`, `sample_count`, `kill_switch_seen`) que l'exécuteur réel, sans dépendre d'un spot PokerTH actionnable.
- Validation réelle supplémentaire : `scripts/debug_arm_window.py` a confirmé sur ce poste que la fenêtre armée voit bien `F10` quand elle est maintenue correctement (`arm_seen=true`, jusqu'à `97/100` échantillons vus sur un run de 5 s). Le problème observé auparavant dans `watch_action_plan.py` n'est donc pas un bug global de détection clavier, mais un problème de synchronisation/protocole autour du vrai spot PokerTH.
- Validation réelle supplémentaire : la priorité du kill switch est maintenant confirmée sur cette même fenêtre armée. Dès que `F12` est vue, la fenêtre se coupe immédiatement, y compris sur des runs où `F10` n'a pas encore eu le temps d'être échantillonnée.
- Validation réelle supplémentaire : `right_shift` n'est pas fiable en contexte PokerTH réel à ce stade. Sur un vrai spot `Call` avec `99` échantillons sur `5 s`, l'exécuteur n'a vu aucun `right_shift` (`arm_seen=false`, `arm_seen_samples=0`) alors que le spot était bien actionnable.
- Validation réelle supplémentaire : `F10` n'est pas fiable non plus en contexte PokerTH réel à ce stade. Sur un vrai spot `Call` avec `100` échantillons sur `5 s`, l'exécuteur n'a vu aucun `F10` (`arm_seen=false`, `arm_seen_samples=0`) alors que cette même touche est bien visible dans `debug_key_state.py` et `debug_arm_window.py` hors contexte PokerTH live.
- Support local ajouté, non encore validé en réel : un panneau visible always-on-top `scripts/control_panel.py` écrit maintenant un état JSON partagé (`paused`, `stopped`, `armed`, `armed_once`) lu par l'exécuteur. Ce chemin doit remplacer les tests d'armement clavier fragiles dès qu'il sera validé sur PokerTH.
- Validation réelle supplémentaire : le panneau visible est maintenant validé en réel sur PokerTH pour le mode `ARM NEXT`. Sur un vrai spot `Call`, l'exécuteur a envoyé `F2`, puis l'état partagé est bien repassé de `armed_once` à `paused`.
- Validation réelle supplémentaire : le chemin d'exécution gardé a été observé en vrai en `autonomous + dry_run`; sur un spot `Call/F2`, le runtime a bien produit `should_execute=true` puis `execution_result.status=dry_run`, sans envoi OS réel.
- Validation réelle supplémentaire : un run `autonomous + armed + --armed-delay-ms 3000` a confirmé le blocage propre hors spot actionnable (`actions=[]`, `target=null`, `execution_result.status=blocked`) et la création du journal auto `data/logs/action_plan/20260423-185818/events.jsonl`.
- Validation réelle supplémentaire : un run `autonomous + armed + --armed-delay-ms 3000` a aussi validé un vrai envoi hotkey simple (`execution_result.status=executed`, `hotkey_sent=F2`) dès qu'un spot `Call` est devenu actionnable.
- Point produit/méthode à retenir : le test kill switch ne doit pas être basé sur "quand le bouton `Call` apparaît", car PokerTH peut exposer des pré-actions avant le vrai moment d'agir. Il faudra un armement explicite pour tester proprement ce garde-fou.
- Validation réelle supplémentaire : l'armement explicite est maintenant observé en vrai. Sur deux vrais spots `Call` actionnables, l'exécution est restée bloquée tant que `F10` n'était pas maintenue pendant le délai armé (`execution_result.status=blocked`, raison `arm key 'f10' non detectee pendant le delai arme`).
- Validation réelle supplémentaire : `watch_action_plan.py` a été observé en vrai sur PokerTH en mode `assist`; les plans `Check` et `Call` générés étaient cohérents, `is_actionable=true`, et la dernière erreur `Aucune fenêtre PokerTH trouvée` venait simplement de la fermeture volontaire de PokerTH par l'utilisateur.
- Validation réelle supplémentaire : `watch_action_plan.py` a aussi été observé en vrai en mode `autonomous`; les états non actionnables restent sans faux plan, et les états actionnables passent bien à `should_execute=true` sans `blocking_issues`.
- Validation utilisateur supplémentaire : le watcher a suivi une même main de `Preflop` à `Flop` puis `Turn`, puis a observé plusieurs changements de `hand_number` et `game_number` avec états globalement cohérents.
- Point technique observé sur un lancement utilisateur standard : Paddle peut encore télécharger ses modèles vers `C:\Users\ArtLi\.paddlex\...` si l'environnement shell n'est pas forcé ; ce n'est pas bloquant pour la lecture, mais l'isolation complète des caches au niveau projet n'est pas encore garantie.
- Dépendances OCR installées et importables dans l'environnement projet : `paddleocr 3.5.0`, `paddle 3.3.1`.
- Contrainte produit confirmée par l'utilisateur : sur les rooms avec temps limité, la décision finale devra inclure non seulement `quoi faire`, mais aussi `quand le faire` et `s'il faut pré-sélectionner une auto-action` (`check`, `call`, etc.) quand l'interface le permet.

---

## 8. Distinction repo / prod / validation

Ce projet n'a pas de "prod" au sens serveur. Les trois états se traduisent :

| État | Signification Ghost-Poker |
|---|---|
| **Repo modifié** | Code local modifié, rien d'autre. |
| **"Prod alignée"** | Le bot tourne réellement sur une table (PokerTH v1, room v2). |
| **Validation réelle** | Une session complète a été observée et les décisions sont correctes. |

Aucun "J terminé" sans validation réelle documentée dans JOURNAL.md.

---

## 9. Décisions structurantes figées (à ne pas re-trancher sans raison)

- **Python** (écosystème poker + vision + ML mature).
- **Hybride perception** (DOM quand dispo, vision sinon).
- **Hybride décision** (solver pour GTO, LLM meta pour exploit).
- **Backend meta interchangeable** : aucune dépendance produit à Mistral/Groq seuls ; l'API ou le modèle local doivent rester remplaçables.
- **Hybride IA** (local gratuit pour perception/solver, API free tier pour démarrer la meta).
- **Mode opératoire sélectionnable** : `assist` ou `autonomous`, pas un seul mode imposé.
- **Contrôle OS réel** (pyautogui + Bézier), pas Playwright visible.
- **A1 avant A2**, non négociable : A2 construit sur des briques validées.
- **Timing d'action et pré-actions** : le moteur final devra gérer un budget temps, des profils de réaction humains non fixes, et l'usage optionnel d'auto-actions quand elles existent sur la room cible.

---

## 10. Budget et contraintes

- **Temps** : pas de deadline, mais le plus vite possible.
- **Argent** : démarrage avec backends gratuits/pratiques (`Mistral`, `Groq`) mais sans verrouiller l'architecture à eux seuls.
  Si ça cale en v2, on doit pouvoir brancher un autre provider API ou un backend local.
- **Compute local** : 4 Go VRAM → pas de LLM local lourd,
  OCR + CV + petits VLM seulement.
