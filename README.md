# ATG_Excel_Pipeline

Automatise le chargement des fichiers Excel JDE **Entrée** (réceptions,
feuille `RDR56REBRE_FR`) et **Sortie** (livraisons, feuille `RDR56REBSL_FR`)
vers PostgreSQL, à la place des deux requêtes Power Query qui ne lisaient
que le fichier le plus récent.

Power BI lira les tables / vues `atg_excel_*`. Les tables ATG existantes
(`tank_measurements`, `file_audit`) ne sont **pas** modifiées.

`Entrée_ATG`, `Sortie_ATG` et `niveau_diff` ne sont **pas** calculés depuis
Excel : ils relèvent d'une vue de jointure ultérieure avec ATG.

## État

Étape en cours : **échafaudage** (config, spécification des colonnes, liaison
d'en-têtes, tests unitaires). Parser, surveillance, chargement SQL : non
implémentés.

## Chemins

Les dossiers se lisent dans `.env` (`ENTREE_DIR`, `SORTIE_DIR`), jamais en dur.

- Production déclarée : `L:\Chris\2026\BI\Entrée` et `\Sortie`.
- Requêtes M actuelles : `D:\SBM\BI_SBM\Entrée` et `\Sortie`.

Copier `.env.example` vers `.env`. Ne jamais y coller le `.env` de
`ATG_SBM_Data_pipeline` (secrets réels). Faire tourner le mot de passe
PostgreSQL si cette archive a circulé.

## Prérequis

Python 3.11+ (Dockerfile du projet ATG existant : 3.12). Windows / PowerShell.

```text
python -m pip install -r requirements-dev.txt
python -m pytest
python -m atg_excel_pipeline check
```

## Conventions reprises de ATG_SBM_Data_pipeline

`get_secret`, SHA-256 par blocs de 1 Mo, journal rotatif, Settings **sans**
lecture d'environnement à l'import du module.

## Sécurité

Aucune valeur de secret n'est journalisée ni affichée par `check`.
