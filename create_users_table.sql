-- Table pour les utilisateurs de TradeFlow
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Activer Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Supprimer les anciennes policies si elles existent
DROP POLICY IF EXISTS "Enable all for anon" ON users;
DROP POLICY IF EXISTS "Enable all for authenticated" ON users;

-- Créer les policies
CREATE POLICY "Enable all for anon"
ON users FOR ALL TO anon USING (true) WITH CHECK (true);

CREATE POLICY "Enable all for authenticated"
ON users FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- Lier les trades aux utilisateurs (ajouter colonne user_email si nécessaire)
-- Cette commande va échouer si la colonne existe déjà, c'est normal
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='trades' AND column_name='user_email') THEN
        ALTER TABLE trades ADD COLUMN user_email TEXT;
    END IF;
END $$;

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_trades_user_email ON trades(user_email);
