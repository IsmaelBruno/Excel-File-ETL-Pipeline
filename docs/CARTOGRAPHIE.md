# Cartographie des sources Excel

Étape B reconfirmée le 2026-10-28. Lecture seule. Fichiers non copiés dans
ce dépôt.

## Chemins

| Origine | Entrée | Sortie |
|---|---|---|
| Requêtes M [Hérité] | `D:\SBM\BI_SBM\Entrée` | `D:\SBM\BI_SBM\Sortie` |
| Production déclarée [Hérité] | `L:\Chris\2026\BI\Entrée` | `L:\Chris\2026\BI\Sortie` |
| Observé sur le poste [Vérifié] | `D:\SBM\BI_SBM\Entrée` et `D:\SBM\BI\Entrée` | idem Sortie |

Un lecteur mappé `L:` n'est pas visible d'un service / tâche planifiée sous un
autre compte : prévoir UNC ou exécution dans la session utilisateur.

## Entrée — `Entrées Sep-26 JdE.xlsx` [Vérifié]

- Feuille `RDR56REBRE_FR` (10 feuilles dans le classeur).
- En-tête ligne **15**, 47 colonnes, `DépôtChargeur`.
- Aligné sur §8 (identités, rangs Date 9/30/34, volumes 15–18).
- Ligne 16 : données métier. `ege` = Volume recu.

## Sortie — `Passage Sep-26 JdE.xlsx` [Vérifié]

- Feuille `RDR56REBSL_FR`.
- En-tête ligne **14**, 39 colonnes (38 + vide).
- `Client` pos. 4 vs `CLIENT` pos. 21 : même normalisation, rangs 1 et 2.
- `egs` = Volume Standard pos. 13. `HHMMSS` = 81717 sur l'échantillon.

## Hors modèle actuel [Vérifié]

- `Entrées Mai-21 JdE.xlsx` : alias `Dépôt Chargeur`, `A3`/`A4`, 46 colonnes.
- `RDR56REBSL_FR_*.xlsb` : autre mise en page (18 colonnes, en-tête 2 lignes).

## Hors périmètre

`Entrée_ATG`, `Sortie_ATG`, `niveau_diff` : absents des feuilles ; source
probable `tank_measurements` (PostgreSQL ATG), vue SQL ultérieure.
