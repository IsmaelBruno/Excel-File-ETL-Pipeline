# ATG_Excel_Pipeline

ETL des fichiers Excel JDE **Entrées** (`RDR56REBRE_FR`) et **Passage**
(`RDR56REBSL_FR`) vers PostgreSQL.

La copie `L:` → `D:\SBM\BI_SBM` est un **autre script**. Ce projet ne fait
qu’extraire, transformer et charger. `EJE 2026.xlsx` est hors périmètre.

Power BI lira les tables `atg_excel_entree`, `atg_excel_sortie`,
`atg_excel_rejets`, `atg_excel_files`. Les tables ATG
(`tank_measurements`, `file_audit`) ne sont pas modifiées.

## Lancer

```powershell
cd D:\SBM\Excel_Input_pipeline
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
copy .env.example .env
```

Dans `.env` : `ENTREE_DIR=D:\SBM\BI_SBM\Entrée`, `SORTIE_DIR=D:\SBM\BI_SBM\Sortie`,
et les variables PostgreSQL (`DB_PASSWORD` ou `DB_PASSWORD_FILE`).

```powershell
python -m pytest
python -m atg_excel_pipeline check
python -m atg_excel_pipeline init-db
python -m atg_excel_pipeline scan-once
python -m atg_excel_pipeline process "D:\SBM\BI_SBM\Entrée\Entrées Sep-26 JdE.xlsx"
```

- `scan-once` : tous les `Entrées*.xlsx` et `Passage*.xlsx` (ignore `EJE*`, `~$*`).
- Même nom redéposé : les lignes de ce fichier sont **remplacées**.
- Nom différent : les lignes **s’ajoutent**.
- Même contenu (SHA-256) déjà `success` : ignoré.

`run` (watchdog) n’est pas dans le périmètre ETL.

## Hors Excel

`Entrée_ATG`, `Sortie_ATG`, `niveau_diff` : vue SQL ultérieure avec ATG.
`Entrées Mai-21 JdE.xlsx` : structure hors modèle → rejet structurel.
