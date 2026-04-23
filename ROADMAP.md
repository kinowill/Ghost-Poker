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
- Sortie normalisée : `TableState` (dataclass).
- Script `scripts/debug_perception.py` qui affiche l'état lu en temps réel.

**Critère de validation** : 20 mains consécutives, état JSON correct à 100 % sur toutes les rues. Diffs visibles dans `JOURNAL.md`.

**État intermédiaire au 2026-04-23** : capture de référence + calibration du layout validées visuellement en plein écran. La capture vise la zone client PokerTH et le layout versionné contient maintenant une taille de référence (`1920×1032`). `scripts/debug_perception.py` est validé en réel sur table ouverte. La stack OCR prévue est maintenant installée ; la prochaine étape utile est d'implémenter la première lecture réelle du contenu.

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

### J4 — Contrôle souris humain ⏳

**But** : exécuter `fold/call/raise/montant` dans PokerTH via souris, de façon non-robotique.

- Courbes Bézier 2D (départ → cible) avec points de contrôle jittered.
- Vitesse variable (ease-in/out).
- Micro-pauses aléatoires avant clic.
- Typage des montants (clavier + backspace occasionnel).
- Test : 100 clics, 0 raté, distribution des trajectoires visuellement humaine.

**Critère de validation** : 10 mains jouées manuellement via le module de contrôle, 0 erreur d'action.

---

### J5 — Boucle complète ⏳

**But** : Perception → Cerveau (solver seul) → Contrôle. Bot joue seul une session.

- Orchestrateur : boucle d'état, anti-double-action, gestion des transitions de rue.
- Solver seul (pas encore de LLM meta).
- Kill switch clavier (ex. `F12` → stop immédiat).
- Logs structurés `loguru` : chaque décision + état + sizing + raisonnement.

**Critère de validation** : **1 session complète de 100 mains** sur PokerTH sans intervention humaine, sans crash, décisions tracées dans `JOURNAL.md`.

---

### J6 — LLM meta (Mistral) pour ajustements exploitatifs ⏳

**But** : couche "lecture des adversaires" par-dessus le solver.

- À la fin de chaque main, stats adversaires mises à jour (VPIP, PFR, agression, showdowns observés).
- Toutes les N mains (ou sur spot critique), appel Mistral avec contexte condensé → retourne des overrides exploitatifs (ex : "HJ fold trop, 3bet light depuis BTN").
- Solver applique les overrides comme biais sur décisions marginales.
- Cache + rate-limit pour tenir sur free tier.

**Critère de validation** : A/B session sans LLM vs avec LLM sur 500 mains, LLM ≥ solver pur sur winrate bb/100 (ou au pire égal sans régression).

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

**J1 — Perception.** Brancher la première lecture utile (pot / board / actions / sièges) en s'appuyant sur la stack OCR désormais installée.
