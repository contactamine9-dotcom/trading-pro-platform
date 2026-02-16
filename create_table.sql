-- ========================================
-- TABLE TRADES POUR TRADING PRO PLATFORM
-- ========================================
-- Copiez-collez ce fichier dans Supabase SQL Editor

CREATE TABLE IF NOT EXISTS trades (
    id BIGSERIAL PRIMARY KEY,
    date TEXT NOT NULL,
    pair TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_price REAL,
    exit_price REAL,
    lots REAL,
    result REAL NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Activer Row Level Security
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;

-- Supprimer les policies existantes si elles existent
DROP POLICY IF EXISTS "Enable all for anon" ON trades;
DROP POLICY IF EXISTS "Enable all for authenticated" ON trades;

-- Policy pour les utilisateurs anonymes (clé anon)
CREATE POLICY "Enable all for anon"
ON trades
FOR ALL
TO anon
USING (true)
WITH CHECK (true);

-- Policy pour les utilisateurs authentifiés
CREATE POLICY "Enable all for authenticated"
ON trades
FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- ========================================
-- FIN DU SCRIPT
-- ========================================
-- Après exécution, vous devriez voir "Success. No rows returned"
