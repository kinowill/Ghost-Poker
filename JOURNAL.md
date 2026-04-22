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

## 2026-04-22 — Ouverture du projet

- **État** : repo modifié uniquement.
- **Ce qui a été fait** :
  - Cadrage projet : cibles A1 (PokerTH play money) puis A2 (rooms en ligne argent réel).
  - Stack figée (Python, `uv`, OCR + CV, solver maison, Mistral API free tier).
  - Création `MASTER.md`, `ROADMAP.md`, `JOURNAL.md`.
  - Repo distant identifié : https://github.com/kinowill/Ghost-Poker (vide).
- **Ce qui a été observé** : rien à runtime. Aucune brique code écrite.
- **Ce qui reste à vérifier** : J0 bootstrap (Python, uv, deps, PokerTH, clé Mistral, git push initial).
- **Commit(s) liés** : aucun (repo local pas encore initialisé).
