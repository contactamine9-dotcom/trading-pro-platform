# 📊 Trading Pro Platform

Application professionnelle de gestion de trading avec calcul de position, journal de trades et analytics avancées.

## 🎯 Fonctionnalités

### 1. Calculateur de Position (Risk Manager)
- Calcul adaptatif par actif (Gold, Indices, Crypto)
- Formule professionnelle : `Position Size = Capital à Risquer / (Distance SL × Valeur Point)`
- Valeur du point pré-configurée et modifiable
- Alertes de risque visuelles (clignotantes)
- Support : XAUUSD, DJ30, DAX40, NAS100, BTCUSD, ETHUSD

### 2. Journal de Trading
- Enregistrement complet des trades
- Base de données cloud Supabase
- Export CSV
- Persistance des données

### 3. Analytics & Performance
- Winrate, Profit Factor, Biggest Win/Loss
- Equity Curve interactive (Plotly)
- Average Win/Loss
- Distribution Gains/Pertes

## 🚀 Technologies

- **Frontend** : Streamlit
- **Base de données** : Supabase (PostgreSQL)
- **Graphiques** : Plotly
- **Data** : Pandas

## 💰 Configuration

- **Capital Réel** : 733.18 €
- **Crédit Broker** : 500.00 €
- **Total Equity** : 1233.18 €
- **Risque par Trade** : 2% (réglable 0.5% - 10%)

## 📦 Installation Locale

```bash
# Cloner le repo
git clone https://github.com/VOTRE-USERNAME/trading-pro-platform.git
cd trading-pro-platform

# Installer les dépendances
pip install -r requirements.txt

# Configurer Supabase
# Créer .streamlit/secrets.toml avec :
[supabase]
url = "VOTRE-SUPABASE-URL"
key = "VOTRE-SUPABASE-ANON-KEY"

# Lancer l'app
streamlit run app.py
```

## 🗄️ Setup Base de Données

Exécuter `create_table.sql` dans Supabase SQL Editor pour créer la table `trades`.

## 🌐 Déploiement

Application déployée sur **Streamlit Cloud** pour une performance optimale.

## 🔒 Sécurité

- Row Level Security (RLS) activé sur Supabase
- Secrets gérés via variables d'environnement
- Clé ANON utilisée (jamais la clé SERVICE_ROLE)

## 📈 Calcul Professionnel

L'application utilise une logique adaptée à chaque type d'actif :
- **Or (XAUUSD)** : 100$/point (100 oz)
- **Indices (DJ30, DAX40, NAS100)** : Valeur configurable
- **Crypto (BTC, ETH)** : 1$/point (1 coin)

## 📊 Interface

Design professionnel type TradingView :
- Mode sombre avec gradients
- Cartes métriques animées
- Alertes clignotantes
- Layout en colonnes

## 📚 Documentation

- `START_HERE.md` - Guide de démarrage rapide
- `SETUP_FINAL.md` - Configuration complète
- `SUPABASE_SETUP.md` - Guide Supabase détaillé
- `DEPLOY_VERCEL.md` - Options de déploiement

## 🎯 Développé pour

Traders professionnels nécessitant :
- Risk management précis
- Suivi de performance
- Calculs adaptés par actif
- Persistance cloud des données

## 📄 Licence

Tous droits réservés - Application de trading professionnelle

---

💹 **Trading Pro Platform** | Professional Risk Management System
