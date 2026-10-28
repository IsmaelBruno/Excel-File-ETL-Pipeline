# Ambiguïtés et règles isolées

Les points ci-dessous ne sont **pas** des règles métier inventées. Ils sont
configurables ou consignés en attendant une validation.

## Confirmé sur fichiers Sep-26 [Vérifié]

- `date_c30` (Entrée pos. 30) peut contenir du texte (`ABESPTOTAL`) : conversion
  date en NULL + comptage, **sans rejet de ligne**.
- Heure Entrée (pos. 31) observée comme `datetime.time` : le parseur tolérant
  (§10) reste nécessaire ; d'autres formats (HHMMSS, fraction Excel) n'ont pas
  encore été vus sur ce fichier.
- Identifiants Excel parfois numériques (`N° Bon`, `Client`, `N° BSL`) : stockage
  texte / entier selon spec, **sans** `.0` pour les codes texte.
- Sortie : 39ᵉ colonne vide après les 38 spécifiées — ignorée.
- `T°` et `Densité à 15` lus comme texte avec **point** décimal (`11.50`).

## À valider métier

1. **`Entrées Mai-21 JdE.xlsx`** : en-tête `Dépôt Chargeur`, `A3`/`A4`, `OR/PS`
   absent, ligne suivant l'en-tête = sous-titres. Rejet structurel probable.
   Faut-il un profil historique ?
2. **Fichiers `.xlsb` JDE bruts** (ex. `RDR56REBSL_FR_*.xlsb`) : feuille au nom
   suffixé, en-tête sur **deux lignes**, 18 colonnes, dates série Excel.
   **Hypothèse [Supposé]** : rejet jusqu'à décision (feuille ≠ `RDR56REBSL_FR`).
3. **Arrondi entier Sortie** (`n_bsl`, `comm`, `n_ot`) : `ROUND_HALF_EVEN`
   [Hérité, à vérifier sur valeurs en `.5`].
4. Sens métier des colonnes suffixées `_cNN` (`n_commande_c3`/`c5`, volumes
   amb/std c15–c18, `date_c30`) : **aucune interprétation**.
5. Formule ou jointure `Entrée_ATG` / `Sortie_ATG` / `niveau_diff` : hors
   périmètre Excel ; vue SQL ultérieure sur `tank_measurements`.

## Options de repli (défaut false)

- `ALLOW_HEADER_FALLBACK` : ligne 14 (Entrée) / 13 (Sortie) si marqueur absent.
- `ALLOW_FIRST_SHEET_FALLBACK` : 1ʳᵉ feuille si `RDR56REBRE_FR` / `RDR56REBSL_FR`
  absente.
