# Ghost-Poker — Document maître

> Référence opérative du projet. Lu seul, ce fichier doit donner
> une image exacte de Ghost-Poker à l'instant T.
> Mis à jour à chaque session qui modifie la vérité du projet.

**Repo distant** : https://github.com/kinowill/Ghost-Poker (vide, à peupler au premier push)
**Dossier local** : `C:\PROJETS\POKER\` (à renommer éventuellement en `Ghost-Poker` si souhaité)

---

## 1. Nom et but

**Ghost-Poker** — agent IA qui joue au poker en ligne de manière
ultra optimisée, en percevant la table (DOM + vision) et en contrôlant
la souris comme un humain.

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
- **Décision produit assumée** : l'utilisateur est informé, conscient,
  et pilote. Ghost-Poker assiste le choix, ne le tranche pas.

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
| LLM meta | `mistralai` SDK (free tier Mistral La Plateforme) | Lecture villain, ajustements exploitatifs |
| LLM fallback | Groq API (Llama 3.3 70B free) | Si Mistral rate-limit |
| Contrôle OS | `pyautogui` + courbes Bézier maison + jitter temporel | Clics humains |
| Tests | `pytest` | Unitaires + intégration |
| Logs | `loguru` | Journal structuré |

**Hardware cible** (machine utilisateur) :
Ryzen 5 5600H, 16 Go RAM, RTX 3050 Laptop 4 Go VRAM, SSD 477 Go, Windows 11.
→ Tout le local (OCR, CV, petits VLM quantisés, solver) passe.
Gros LLM = API.

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
                                          [Contrôle souris humain]
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
│       ├── brain/         # solver + LLM meta
│       ├── control/       # souris / clavier humains
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
   une fois le premier push effectué. Tant que vide, non-authoritaire.

---

## 7. État courant (à maintenir à jour)

**Date** : 2026-04-23
**Phase** : J1 — Perception (capture + OCR → état table JSON).

**J0 clos ✅** (toutes cases cochées, PokerTH confirmé fonctionnel par l'utilisateur).

**J1.1 + J1.2 validés** : capture de référence réalisée, layout recalibré puis validé visuellement en plein écran. `data/config/pokerth_layout.json` contient maintenant 15 zones, dont `table_meta`, plus les métadonnées de référence.

**J1.3 validé en réel** : `scripts/debug_perception.py` capture bien la table PokerTH ouverte, découpe les 15 zones, sauvegarde les crops et écrit un résumé JSON sans alerte de géométrie.

**Première lecture OCR branchée, validation partielle** : `src/ghost_poker/perception/ocr.py` et `table_state.py` lisent maintenant une première version structurée de `table_meta`, `pot`, `actions` et des sièges. Validation réelle observée sur PokerTH : `street=Preflop`, `game=1`, `hand=1`, `pot.total=0`, `pot.bets=110`, `seat_1..seat_10` relus avec noms/stacks cohérents sur la main testée, et panneau d'action relu correctement (`All-In/F4`, presets `33/50/100`, `Raise/F3/$40`, `Call/F2/$20`, `Fold/F1`).

**Prochain pas immédiat** : stabiliser cette lecture sur plusieurs mains consécutives via le watcher léger, qui journalise maintenant automatiquement ses changements d'état en JSONL, puis traiter les éléments encore incomplets ou non fiables (cartes hero/board, historique d'action détaillé, éventuelle zone `journal_log` optionnelle pour PokerTH).

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
- **Hybride IA** (local gratuit pour perception/solver, API free tier pour LLM).
- **Contrôle OS réel** (pyautogui + Bézier), pas Playwright visible.
- **A1 avant A2**, non négociable : A2 construit sur des briques validées.
- **Timing d'action et pré-actions** : le moteur final devra gérer un budget temps, des profils de réaction humains non fixes, et l'usage optionnel d'auto-actions quand elles existent sur la room cible.

---

## 10. Budget et contraintes

- **Temps** : pas de deadline, mais le plus vite possible.
- **Argent** : API free tiers uniquement au départ (Mistral + Groq).
  Si ça cale sur rate limits en v2, on évalue le passage payant.
- **Compute local** : 4 Go VRAM → pas de LLM local lourd,
  OCR + CV + petits VLM seulement.
