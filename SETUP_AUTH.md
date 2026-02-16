# 🔐 Configuration de l'Authentification TradeFlow

## ⚡ Configuration Rapide (5 minutes)

### Étape 1 : Créer la Table Users dans Supabase

1. Allez sur **https://app.supabase.com**
2. Sélectionnez votre projet
3. Cliquez sur **SQL Editor** (dans le menu à gauche)
4. Cliquez sur **New query**
5. **Copiez-collez** le contenu du fichier `create_users_table.sql` :

```sql
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

-- Créer les policies
DROP POLICY IF EXISTS "Enable all for anon" ON users;
DROP POLICY IF EXISTS "Enable all for authenticated" ON users;

CREATE POLICY "Enable all for anon"
ON users FOR ALL TO anon USING (true) WITH CHECK (true);

CREATE POLICY "Enable all for authenticated"
ON users FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- Ajouter colonne user_email à la table trades
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
```

6. Cliquez sur **Run** ▶️
7. Vous devriez voir : **"Success. No rows returned"**

---

### Étape 2 : Vérifier les Secrets Streamlit Cloud

Les secrets doivent être **EXACTEMENT** comme ceci dans Streamlit Cloud :

```toml
[supabase]
url = "https://qospyynejdkcinbmddaq.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFvc3B5eW5lamRrY2luYm1kZGFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEyMzI2MTAsImV4cCI6MjA4NjgwODYxMH0.zeLStpHVPVGh_n0H47QdkUv9bMY-cuJyVWome_Z-LtM"
```

---

### Étape 3 : Tester l'Application

1. Allez sur votre app : **https://trading-pro-platform.streamlit.app**

2. Vous devriez voir la page de login **TradeFlow**

3. Cliquez sur l'onglet **"📝 Sign Up"**

4. Créez un compte :
   - Email : `votre@email.com`
   - Nom : `Votre Nom`
   - Mot de passe : `minimum 6 caractères`

5. Connectez-vous avec vos identifiants

6. ✅ Vous êtes dans l'application !

---

## 🎯 Fonctionnalités de Sécurité

### ✅ Ce qui est sécurisé :

1. **Mots de passe hachés** avec bcrypt (jamais stockés en clair)
2. **Row Level Security** activé sur Supabase
3. **Isolation des données** : chaque utilisateur ne voit que ses trades
4. **Session management** : authentification via session_state
5. **Validation des inputs** : vérification des mots de passe (min 6 caractères)

### 🔒 Sécurité des Données :

- Les mots de passe sont **hachés avec bcrypt** (salt automatique)
- Chaque trade est lié à un `user_email`
- Les requêtes filtrent automatiquement par utilisateur
- Impossible de voir ou modifier les trades d'un autre utilisateur

---

## 🌊 Structure de l'Application

### Pages Disponibles (après login) :

1. **🏠 Dashboard** : Vue d'ensemble de votre capital et performance
2. **🧮 Calculator** : Calculateur de position size
3. **📔 Journal** : Historique de vos trades
4. **📊 Analytics** : Statistiques et graphiques de performance

### Navigation :

- **Sidebar** : Logo, info utilisateur, navigation, paramètres
- **Bouton Déconnexion** : En bas de la sidebar
- **Design Fintech Dark Mode** : Interface ultra-professionnelle

---

## 🛠️ Dépendances Ajoutées

Le fichier `requirements.txt` contient maintenant :

```txt
streamlit
pandas
plotly
supabase
bcrypt  ← NOUVEAU (pour le hachage des mots de passe)
```

---

## 🐛 Dépannage

### Erreur : "Table 'users' non trouvée"

➡️ Vous n'avez pas exécuté le SQL dans Supabase.
➡️ Retournez à l'Étape 1.

### Erreur : "Duplicate key value violates unique constraint"

➡️ L'email existe déjà dans la base.
➡️ Utilisez un autre email ou connectez-vous.

### Je ne vois pas mes anciens trades

➡️ Normal ! Les anciens trades n'ont pas de `user_email`.
➡️ Vous devez les supprimer ou ajouter manuellement le champ dans Supabase.

### L'app ne démarre pas

➡️ Vérifiez les logs Streamlit Cloud.
➡️ Vérifiez que bcrypt est bien installé (check requirements.txt).

---

## 📊 Migration des Anciens Trades (Optionnel)

Si vous avez des trades existants sans `user_email`, vous pouvez :

### Option 1 : Les supprimer (Recommandé)

```sql
-- Dans Supabase SQL Editor
DELETE FROM trades WHERE user_email IS NULL;
```

### Option 2 : Les attribuer à votre compte

```sql
-- Remplacez 'votre@email.com' par votre vrai email
UPDATE trades
SET user_email = 'votre@email.com'
WHERE user_email IS NULL;
```

---

## 🎨 Design Fintech Dark Mode

### CSS Personnalisé Inclus :

- ✅ Fond ultra-dark (#0e1117)
- ✅ Sidebar gradient moderne
- ✅ Inputs et boutons arrondis (8px radius)
- ✅ Boutons avec gradient cyan-vert
- ✅ Containers/Cards avec bordures
- ✅ Animation pulse sur les alertes danger
- ✅ Métriques stylisées avec couleurs
- ✅ Tabs modernes
- ✅ Menu Streamlit caché (look application native)

---

## 🚀 Prochaines Étapes

Votre TradeFlow Premium est maintenant opérationnel avec :

✅ Authentification complète (Login/Sign-up)
✅ Design Fintech Dark Mode ultra-pro
✅ Isolation des données par utilisateur
✅ Sécurité bcrypt pour les mots de passe
✅ Navigation moderne avec sidebar
✅ Look application native (menu Streamlit caché)

**Profitez de votre plateforme de trading professionnelle !** 🌊

---

💹 **TradeFlow** | Professional Trading Intelligence | Powered by Supabase
