-- Chevauchement de périodes entre fichiers de noms différents (avertissement, pas de suppression).
SELECT a.source_name AS fichier_a,
       b.source_name AS fichier_b,
       a.flow,
       a.date_min AS a_min,
       a.date_max AS a_max,
       b.date_min AS b_min,
       b.date_max AS b_max
FROM atg_excel_files a
JOIN atg_excel_files b
  ON a.flow = b.flow
 AND a.status = 'success'
 AND b.status = 'success'
 AND a.id < b.id
 AND a.source_name <> b.source_name
 AND a.date_min IS NOT NULL
 AND b.date_min IS NOT NULL
 AND a.date_min <= b.date_max
 AND a.date_max >= b.date_min;
