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

**Date** : 2026-04-22
**Phase** : J0 — Bootstrap projet.

- ✅ MASTER / ROADMAP / JOURNAL créés (session du 2026-04-22).
- ⏳ Installation environnement Python + `uv` + deps — non commencée.
- ⏳ Installation PokerTH (banc de test A1) — non commencée.
- ⏳ Dépôt git — non initialisé.
- ⏳ Clé API Mistral (free tier) — non créée.

**Prochain pas immédiat** : J0 — bootstrap (voir ROADMAP.md).

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

---

## 10. Budget et contraintes

- **Temps** : pas de deadline, mais le plus vite possible.
- **Argent** : API free tiers uniquement au départ (Mistral + Groq).
  Si ça cale sur rate limits en v2, on évalue le passage payant.
- **Compute local** : 4 Go VRAM → pas de LLM local lourd,
  OCR + CV + petits VLM seulement.
