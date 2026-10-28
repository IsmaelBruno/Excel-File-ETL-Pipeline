-- Tables Excel JDE. Ne pas modifier tank_measurements / file_audit.
CREATE TABLE IF NOT EXISTS atg_excel_files (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(512) NOT NULL,
    source_path VARCHAR(1024) NOT NULL,
    flow VARCHAR(16) NOT NULL,
    file_sha256 CHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    sheet_name VARCHAR(128),
    header_row INTEGER,
    rows_read INTEGER NOT NULL DEFAULT 0,
    valid_rows INTEGER NOT NULL DEFAULT 0,
    rejected_rows INTEGER NOT NULL DEFAULT 0,
    rows_blank_skipped INTEGER NOT NULL DEFAULT 0,
    cell_errors INTEGER NOT NULL DEFAULT 0,
    conversion_errors INTEGER NOT NULL DEFAULT 0,
    duplicate_rows INTEGER NOT NULL DEFAULT 0,
    date_min DATE,
    date_max DATE,
    error_message TEXT,
    processed_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS atg_excel_entree (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(512) NOT NULL,
    source_row INTEGER NOT NULL,
    depot_chargeur TEXT,
    produit TEXT,
    n_commande_c3 TEXT,
    n_bon TEXT,
    n_commande_c5 TEXT,
    or_ps TEXT,
    client TEXT,
    n_commande_reception TEXT,
    date_principale DATE,
    type TEXT,
    n_c11 TEXT,
    transporteur TEXT,
    ege DOUBLE PRECISION,
    volume_standard DOUBLE PRECISION,
    volume_amb_c15 DOUBLE PRECISION,
    volume_std_c16 DOUBLE PRECISION,
    volume_amb_c17 DOUBLE PRECISION,
    volume_std_c18 DOUBLE PRECISION,
    a1 TEXT,
    a2 TEXT,
    dep TEXT,
    dist TEXT,
    perte_dech DOUBLE PRECISION,
    date_c30 DATE,
    heure TIME,
    UNIQUE (source_name, source_row)
);

CREATE TABLE IF NOT EXISTS atg_excel_sortie (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(512) NOT NULL,
    source_row INTEGER NOT NULL,
    depot_livrancier TEXT,
    produit TEXT,
    n_cf_client TEXT,
    client TEXT,
    n_bsl INTEGER,
    n_commande_jde TEXT,
    date_livraison DATE,
    type TEXT,
    n_vehicule TEXT,
    transporteur TEXT,
    volume_amb DOUBLE PRECISION,
    egs DOUBLE PRECISION,
    n_bac_livraison TEXT,
    temperature DOUBLE PRECISION,
    densite_15 DOUBLE PRECISION,
    city TEXT,
    a1 TEXT,
    site_chargeur TEXT,
    client_c21 TEXT,
    site_dest TEXT,
    tcde TEXT,
    comm INTEGER,
    n_ot INTEGER,
    heure TIME,
    UNIQUE (source_name, source_row)
);

CREATE TABLE IF NOT EXISTS atg_excel_rejets (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(512) NOT NULL,
    source_row INTEGER NOT NULL,
    flow VARCHAR(16) NOT NULL,
    motif VARCHAR(64) NOT NULL,
    raw_json TEXT,
    UNIQUE (source_name, source_row, flow)
);

CREATE INDEX IF NOT EXISTS idx_atg_excel_entree_date ON atg_excel_entree (date_principale);
CREATE INDEX IF NOT EXISTS idx_atg_excel_sortie_date ON atg_excel_sortie (date_livraison);
CREATE INDEX IF NOT EXISTS idx_atg_excel_files_name ON atg_excel_files (source_name, status);
