import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client

# Configuration de la page
st.set_page_config(
    page_title="TradeFlow",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS professionnel avec effet clignotant
st.markdown("""
    <style>
    /* Cacher les éléments Streamlit pour un look application native */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Theme sombre professionnel */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
    }

    /* Conteneurs de métriques personnalisés */
    .metric-card {
        background: linear-gradient(135deg, #1e2530 0%, #2a3142 100%);
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #2a3f5f;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        text-align: center;
        margin: 10px 0;
        transition: transform 0.2s;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #00ff88;
    }

    .metric-label {
        color: #8b92a7;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }

    .metric-value {
        color: #ffffff;
        font-size: 32px;
        font-weight: 700;
        margin: 10px 0;
    }

    .metric-value-success {
        color: #00ff88;
    }

    .metric-value-warning {
        color: #ffaa00;
    }

    .metric-value-danger {
        color: #ff4444;
    }

    /* Alerte danger clignotante */
    @keyframes blink-red {
        0%, 50%, 100% {
            background-color: rgba(255, 68, 68, 0.2);
            border-color: #ff4444;
        }
        25%, 75% {
            background-color: rgba(255, 68, 68, 0.6);
            border-color: #ff0000;
        }
    }

    .danger-alert {
        animation: blink-red 1.5s infinite;
        background-color: rgba(255, 68, 68, 0.2);
        border: 2px solid #ff4444;
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
    }

    .danger-alert h2 {
        color: #ff4444;
        font-size: 24px;
        font-weight: bold;
        margin: 0;
    }

    .danger-alert p {
        color: #ffcccc;
        font-size: 16px;
        margin: 10px 0 0 0;
    }

    /* Section header */
    .section-header {
        background: linear-gradient(90deg, #00ff88 0%, #00d4ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 28px;
        font-weight: 800;
        margin: 20px 0 15px 0;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* Info box */
    .info-box {
        background: linear-gradient(135deg, #1e2530 0%, #2a3142 100%);
        border-left: 4px solid #00ff88;
        padding: 15px 20px;
        border-radius: 10px;
        margin: 15px 0;
    }

    .info-box-label {
        color: #8b92a7;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .info-box-value {
        color: #ffffff;
        font-size: 24px;
        font-weight: 700;
        margin-top: 5px;
    }

    /* Divider */
    hr {
        border: none;
        border-top: 1px solid #2a3f5f;
        margin: 30px 0;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00ff88 0%, #00d4ff 100%);
        color: #0a0e27;
        font-weight: 700;
        border: none;
        border-radius: 10px;
        padding: 12px 30px;
        transition: all 0.3s;
    }

    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
    }

    /* Sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f3a 0%, #0a0e27 100%);
    }

    /* DataFrames */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #1e2530;
        border-radius: 10px 10px 0 0;
        padding: 12px 24px;
        color: #8b92a7;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00ff88 0%, #00d4ff 100%);
        color: #0a0e27;
    }
    </style>
""", unsafe_allow_html=True)

# Configuration des actifs avec valeurs de point prédéfinies
ASSET_CONFIG = {
    "XAUUSD": {
        "name": "Gold",
        "point_value": 100.0,
        "currency": "$",
        "contract_size": "100 oz",
        "description": "1 point = 100$ par lot standard"
    },
    "DJ30": {
        "name": "Dow Jones 30",
        "point_value": 5.0,
        "currency": "$",
        "contract_size": "1 point = 5$",
        "description": "Valeur typique: 1-5$ par point"
    },
    "DAX40": {
        "name": "DAX 40",
        "point_value": 25.0,
        "currency": "€",
        "contract_size": "1 point = 25€",
        "description": "Valeur typique: 1-25€ par point"
    },
    "NAS100": {
        "name": "Nasdaq 100",
        "point_value": 20.0,
        "currency": "$",
        "contract_size": "1 point = 20$",
        "description": "Valeur typique: 1-20$ par point"
    },
    "BTCUSD": {
        "name": "Bitcoin",
        "point_value": 1.0,
        "currency": "$",
        "contract_size": "1 coin",
        "description": "1$ move = 1$ PnL par coin"
    },
    "ETHUSD": {
        "name": "Ethereum",
        "point_value": 1.0,
        "currency": "$",
        "contract_size": "1 coin",
        "description": "1$ move = 1$ PnL par coin"
    }
}

# ============================================
# CONNEXION SUPABASE
# ============================================
@st.cache_resource
def init_supabase():
    """Initialise la connexion Supabase avec gestion d'erreurs"""
    try:
        import os

        # Priorité 1: Variables d'environnement (pour Vercel/Heroku/etc)
        # Priorité 2: st.secrets (pour Streamlit Cloud et local)
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        # Si pas de variables d'env, essayer st.secrets
        if not supabase_url or not supabase_key:
            if "supabase" not in st.secrets:
                st.error("""
                ❌ **Configuration manquante**

                Veuillez configurer Supabase via :
                - Variables d'environnement : SUPABASE_URL et SUPABASE_KEY
                OU
                - Fichier `.streamlit/secrets.toml` avec :
                ```toml
                [supabase]
                url = "https://VOTRE-PROJECT-ID.supabase.co"
                key = "VOTRE-SUPABASE-ANON-KEY"
                ```
                """)
                st.stop()

            supabase_url = st.secrets["supabase"]["url"]
            supabase_key = st.secrets["supabase"]["key"]

        # Vérifier que ce ne sont pas les valeurs par défaut
        if "VOTRE" in supabase_url or "VOTRE" in supabase_key:
            st.error("""
            ❌ **Clés Supabase non configurées**

            Remplacez les valeurs par défaut dans `.streamlit/secrets.toml` par vos vraies clés Supabase.

            **Comment obtenir vos clés :**
            1. Allez sur https://app.supabase.com
            2. Sélectionnez votre projet
            3. Allez dans Settings > API
            4. Copiez "Project URL" et "anon public key"
            """)
            st.stop()

        # Créer le client Supabase
        supabase: Client = create_client(supabase_url, supabase_key)

        return supabase

    except Exception as e:
        st.error(f"""
        ❌ **Erreur de connexion à Supabase**

        {str(e)}

        Vérifiez vos clés dans `.streamlit/secrets.toml`
        """)
        st.stop()

# Initialiser Supabase
supabase = init_supabase()

# ============================================
# VÉRIFICATION DE LA TABLE
# ============================================
def check_table_exists():
    """Vérifie si la table 'trades' existe et affiche un message si nécessaire"""
    try:
        # Essayer de faire une requête simple avec timeout implicite
        result = supabase.table('trades').select("id").limit(1).execute()
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if "relation" in error_msg and "does not exist" in error_msg:
            st.warning("""
            ⚠️ **Table 'trades' non trouvée dans Supabase**

            **Instructions rapides :**
            1. Allez sur https://app.supabase.com
            2. Sélectionnez votre projet
            3. Allez dans "SQL Editor"
            4. Exécutez le fichier `create_table.sql`
            5. Rafraîchissez cette page

            **SQL à exécuter :**
            ```sql
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
            ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
            CREATE POLICY "Enable all for anon" ON trades FOR ALL TO anon USING (true) WITH CHECK (true);
            CREATE POLICY "Enable all for authenticated" ON trades FOR ALL TO authenticated USING (true) WITH CHECK (true);
            ```
            """)
            return False
        else:
            st.warning(f"⚠️ Erreur de connexion Supabase : {str(e)[:200]}")
            return False

# Vérifier que la table existe au démarrage (avec timeout pour éviter blocage)
try:
    check_table_exists()
except Exception as e:
    st.warning(f"⚠️ Impossible de vérifier la table 'trades'. Erreur : {str(e)[:100]}")
    st.info("L'application va démarrer quand même. Vérifiez votre connexion Supabase.")

# ============================================
# FONCTIONS SUPABASE
# ============================================
def add_trade(date, pair, direction, entry_price, exit_price, lots, result):
    """Ajoute un trade dans Supabase"""
    try:
        data = {
            "date": date,
            "pair": pair,
            "direction": direction,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "lots": lots,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        response = supabase.table('trades').insert(data).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erreur lors de l'ajout du trade : {str(e)}")
        return False

def get_all_trades():
    """Récupère tous les trades depuis Supabase, triés par date décroissante"""
    try:
        response = supabase.table('trades').select("*").order('date', desc=True).execute()
        if response.data:
            return pd.DataFrame(response.data)
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération des trades : {str(e)}")
        return pd.DataFrame()

def delete_all_trades():
    """Supprime tous les trades de Supabase"""
    try:
        # Récupérer tous les IDs
        response = supabase.table('trades').select("id").execute()
        if response.data:
            for trade in response.data:
                supabase.table('trades').delete().eq('id', trade['id']).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erreur lors de la suppression des trades : {str(e)}")
        return False

def calculate_kpis(trades_df):
    """Calcule les KPIs à partir du DataFrame des trades"""
    if trades_df.empty:
        return {
            'winrate': 0,
            'profit_factor': 0,
            'biggest_win': 0,
            'biggest_loss': 0,
            'total_trades': 0,
            'avg_win': 0,
            'avg_loss': 0
        }

    winning_trades = trades_df[trades_df['result'] > 0]
    losing_trades = trades_df[trades_df['result'] < 0]

    total_wins = winning_trades['result'].sum() if not winning_trades.empty else 0
    total_losses = abs(losing_trades['result'].sum()) if not losing_trades.empty else 0

    winrate = (len(winning_trades) / len(trades_df)) * 100 if len(trades_df) > 0 else 0
    profit_factor = total_wins / total_losses if total_losses > 0 else (total_wins if total_wins > 0 else 0)

    avg_win = winning_trades['result'].mean() if not winning_trades.empty else 0
    avg_loss = losing_trades['result'].mean() if not losing_trades.empty else 0

    return {
        'winrate': winrate,
        'profit_factor': profit_factor,
        'biggest_win': trades_df['result'].max() if not trades_df.empty else 0,
        'biggest_loss': trades_df['result'].min() if not trades_df.empty else 0,
        'total_trades': len(trades_df),
        'avg_win': avg_win,
        'avg_loss': avg_loss
    }

# ============================================
# SIDEBAR - PARAMÈTRES DU COMPTE
# ============================================
# Logo et branding
try:
    st.sidebar.image("logo.png", use_column_width=True)
except:
    st.sidebar.markdown('<h1 style="color: #00ff88; text-align: center;">🌊 TradeFlow</h1>', unsafe_allow_html=True)

st.sidebar.markdown('<p style="text-align: center; color: #8b92a7; font-size: 13px; margin-top: -10px;">Professional Trading Intelligence</p>', unsafe_allow_html=True)
st.sidebar.markdown("---")

st.sidebar.markdown('<h2 style="color: #00ff88; text-align: center; font-size: 18px;">⚙️ ACCOUNT</h2>', unsafe_allow_html=True)
st.sidebar.markdown("---")

# Capital
capital_reel = st.sidebar.number_input(
    "💰 Capital Réel (€)",
    min_value=0.0,
    value=733.18,
    step=50.0,
    help="Votre capital personnel"
)

credit_broker = st.sidebar.number_input(
    "🏦 Crédit Broker (€)",
    min_value=0.0,
    value=500.0,
    step=50.0,
    help="Crédit non retirable mais utilisable pour la marge"
)

capital_total = capital_reel + credit_broker

st.sidebar.markdown(f"""
<div class="info-box">
    <div class="info-box-label">Total Equity</div>
    <div class="info-box-value" style="color: #00ff88;">{capital_total:.2f} €</div>
    <div style="color: #8b92a7; font-size: 12px; margin-top: 10px;">
        Réel: {capital_reel:.2f}€ | Crédit: {credit_broker:.2f}€
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

# Risque
risque_pct = st.sidebar.slider(
    "🎯 Risque par Trade (%)",
    min_value=0.5,
    max_value=10.0,
    value=2.0,
    step=0.5,
    help="Pourcentage du capital total à risquer"
)

montant_risque_total = capital_total * (risque_pct / 100)

risk_color = "#00ff88" if risque_pct <= 5 else "#ff4444"

st.sidebar.markdown(f"""
<div class="info-box" style="border-left-color: {risk_color};">
    <div class="info-box-label">Risque par Trade</div>
    <div class="info-box-value" style="color: {risk_color};">{montant_risque_total:.2f} €</div>
    <div style="color: #8b92a7; font-size: 12px; margin-top: 5px;">
        {risque_pct}% du capital total
    </div>
</div>
""", unsafe_allow_html=True)

# Indicateur de connexion Supabase
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align: center; padding: 10px; background-color: rgba(0, 255, 136, 0.1); border-radius: 10px; border: 1px solid #00ff88;">
    <small style="color: #00ff88;">✅ Connecté à Supabase</small>
</div>
""", unsafe_allow_html=True)

# ============================================
# HEADER PRINCIPAL
# ============================================
st.markdown('<h1 style="text-align: center; color: #00ff88; font-size: 48px; font-weight: 900; margin-bottom: 0;">🌊 TRADEFLOW</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #8b92a7; font-size: 16px; margin-top: 10px;">Professional Trading Intelligence | Risk Management & Analytics</p>', unsafe_allow_html=True)

# Dashboard metrics (3 colonnes pour les infos clés)
dash_col1, dash_col2, dash_col3 = st.columns(3)

with dash_col1:
    st.metric(
        label="💰 Capital Réel",
        value=f"{capital_reel:.2f} €",
        delta=None
    )

with dash_col2:
    st.metric(
        label="🏦 Crédit Broker",
        value=f"{credit_broker:.2f} €",
        delta=None
    )

with dash_col3:
    st.metric(
        label="💎 Total Equity",
        value=f"{capital_total:.2f} €",
        delta=f"{risque_pct}% risk/trade"
    )

st.markdown("---")

# ============================================
# ONGLETS
# ============================================
tab1, tab2, tab3 = st.tabs(["🎯 POSITION CALCULATOR", "📔 TRADE JOURNAL", "📊 ANALYTICS"])

# ============================================
# TAB 1 : CALCULATEUR DE POSITION
# ============================================
with tab1:
    st.markdown('<div class="section-header">⚡ Risk Calculator</div>', unsafe_allow_html=True)

    # Layout en colonnes (style TradingView)
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("### 🎲 Trade Parameters")

        # Sélection de l'actif
        selected_pair = st.selectbox(
            "Asset",
            options=list(ASSET_CONFIG.keys()),
            format_func=lambda x: f"{x} - {ASSET_CONFIG[x]['name']}"
        )

        asset_info = ASSET_CONFIG[selected_pair]

        # Info sur l'actif sélectionné
        st.info(f"📌 **{asset_info['name']}** | {asset_info['description']}")

        # Prix d'entrée
        entry_price = st.number_input(
            "Entry Price",
            min_value=0.0,
            value=2000.0 if "XAU" in selected_pair else 1.1000,
            step=0.01 if "BTC" in selected_pair or "ETH" in selected_pair else 0.0001,
            format="%.4f"
        )

        # Stop Loss
        stop_loss = st.number_input(
            "Stop Loss",
            min_value=0.0,
            value=1950.0 if "XAU" in selected_pair else 1.0950,
            step=0.01 if "BTC" in selected_pair or "ETH" in selected_pair else 0.0001,
            format="%.4f"
        )

        # Take Profit
        take_profit = st.number_input(
            "Take Profit",
            min_value=0.0,
            value=2100.0 if "XAU" in selected_pair else 1.1100,
            step=0.01 if "BTC" in selected_pair or "ETH" in selected_pair else 0.0001,
            format="%.4f"
        )

        st.markdown("---")

        # Valeur du point (modifiable)
        st.markdown("### ⚙️ Contract Specifications")

        point_value = st.number_input(
            f"Point Value ({asset_info['currency']})",
            min_value=0.01,
            value=asset_info['point_value'],
            step=0.01 if asset_info['point_value'] < 10 else 1.0,
            help=f"Valeur prédéfinie: {asset_info['point_value']}{asset_info['currency']}. Ajustez selon votre broker (mini/micro lots)."
        )

        st.caption(f"💡 Contract: {asset_info['contract_size']}")

    with col_right:
        st.markdown("### 📊 Position Sizing Results")

        # Calculs
        if entry_price > 0 and stop_loss > 0 and take_profit > 0 and point_value > 0:
            # Distance en points
            risk_distance = abs(entry_price - stop_loss)
            reward_distance = abs(take_profit - entry_price)

            # Calcul de la taille de position selon la formule professionnelle
            # Position Size (Lots) = Capital à Risquer / (Distance Stop Loss × Valeur du Point)
            if risk_distance > 0:
                position_size_lots = montant_risque_total / (risk_distance * point_value)
            else:
                position_size_lots = 0

            # Calcul du P&L
            perte_max = risk_distance * point_value * position_size_lots
            gain_potentiel = reward_distance * point_value * position_size_lots

            # Ratio R:R
            risk_reward_ratio = reward_distance / risk_distance if risk_distance > 0 else 0

            # Vérifications de risque
            risk_exceeds = risque_pct > 5
            credit_impacted = perte_max > capital_reel

            # Affichage des métriques
            metric_col1, metric_col2 = st.columns(2)

            with metric_col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Position Size</div>
                    <div class="metric-value metric-value-success">{position_size_lots:.4f}</div>
                    <div style="color: #8b92a7; font-size: 14px;">Lots</div>
                </div>
                """, unsafe_allow_html=True)

            with metric_col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Risk:Reward</div>
                    <div class="metric-value {'metric-value-success' if risk_reward_ratio >= 2 else 'metric-value-warning'}">
                        1:{risk_reward_ratio:.2f}
                    </div>
                    <div style="color: #8b92a7; font-size: 14px;">Ratio</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            metric_col3, metric_col4 = st.columns(2)

            with metric_col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Maximum Loss</div>
                    <div class="metric-value metric-value-danger">-{perte_max:.2f} €</div>
                    <div style="color: #8b92a7; font-size: 14px;">{risk_distance:.4f} points</div>
                </div>
                """, unsafe_allow_html=True)

            with metric_col4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Potential Gain</div>
                    <div class="metric-value metric-value-success">+{gain_potentiel:.2f} €</div>
                    <div style="color: #8b92a7; font-size: 14px;">{reward_distance:.4f} points</div>
                </div>
                """, unsafe_allow_html=True)

            # Alertes de risque
            if risk_exceeds or credit_impacted:
                st.markdown("<br>", unsafe_allow_html=True)
                alert_messages = []
                if risk_exceeds:
                    alert_messages.append(f"⚠️ Le risque de {risque_pct}% dépasse la limite recommandée de 5%")
                if credit_impacted:
                    alert_messages.append(f"⚠️ La perte potentielle ({perte_max:.2f}€) entamera votre crédit broker")

                st.markdown(f"""
                <div class="danger-alert">
                    <h2>🚨 ALERTE RISQUE ÉLEVÉ</h2>
                    <p>{'<br>'.join(alert_messages)}</p>
                </div>
                """, unsafe_allow_html=True)

            # Détails supplémentaires
            with st.expander("📋 Détails du Calcul"):
                st.markdown(f"""
                **Formule utilisée:**
                ```
                Position Size = Capital à Risquer / (Distance SL × Valeur Point)
                Position Size = {montant_risque_total:.2f} / ({risk_distance:.4f} × {point_value})
                Position Size = {position_size_lots:.4f} lots
                ```

                **Paramètres:**
                - Capital Total: {capital_total:.2f} €
                - Risque: {risque_pct}% = {montant_risque_total:.2f} €
                - Distance Stop Loss: {risk_distance:.4f} points
                - Distance Take Profit: {reward_distance:.4f} points
                - Valeur du Point: {point_value} {asset_info['currency']}

                **P&L Calculation:**
                - Perte Max = {risk_distance:.4f} × {point_value} × {position_size_lots:.4f} = {perte_max:.2f} €
                - Gain Potentiel = {reward_distance:.4f} × {point_value} × {position_size_lots:.4f} = {gain_potentiel:.2f} €
                """)
        else:
            st.warning("⚠️ Veuillez remplir tous les champs pour voir les résultats")

# ============================================
# TAB 2 : JOURNAL DE TRADING
# ============================================
with tab2:
    st.markdown('<div class="section-header">📔 Trade Journal</div>', unsafe_allow_html=True)

    # Récupérer les trades d'abord
    trades_df = get_all_trades()

    # TABLEAU EN PREMIER
    if not trades_df.empty:
        # Préparation du dataframe pour l'affichage
        display_df = trades_df[['date', 'pair', 'direction', 'entry_price', 'exit_price', 'lots', 'result']].copy()
        display_df['result'] = display_df['result'].apply(lambda x: f"{'+' if x > 0 else ''}{x:.2f} €")
        display_df.columns = ['Date', 'Asset', 'Direction', 'Entry', 'Exit', 'Lots', 'P&L']

        # Affichage du tableau interactif
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )

        # Actions
        col_action1, col_action2 = st.columns(2)
        with col_action1:
            if st.button("🗑️ Clear All Trades", type="secondary", use_container_width=True):
                if delete_all_trades():
                    st.success("Tous les trades ont été supprimés de Supabase")
                    st.rerun()

        with col_action2:
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export CSV",
                data=csv,
                file_name=f"trades_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.info("📭 Aucun trade enregistré. Ajoutez votre premier trade ci-dessous!")

    st.markdown("<br>", unsafe_allow_html=True)

    # FORMULAIRE DANS UN EXPANDER FERMÉ
    with st.expander("➕ Nouveau Trade", expanded=False):
        with st.form("trade_form", clear_on_submit=True):
            col_form1, col_form2 = st.columns(2)

            with col_form1:
                trade_date = st.date_input("Date", datetime.now())
                trade_pair = st.selectbox("Asset", list(ASSET_CONFIG.keys()))
                trade_direction = st.radio("Direction", ["Long", "Short"], horizontal=True)
                trade_entry = st.number_input("Entry Price", min_value=0.0, value=0.0, step=0.01)

            with col_form2:
                trade_lots = st.number_input("Lots", min_value=0.0001, value=0.01, step=0.01, format="%.4f")
                trade_exit = st.number_input("Exit Price", min_value=0.0, value=0.0, step=0.01)
                trade_result = st.number_input(
                    "P&L (€)",
                    value=0.0,
                    step=10.0,
                    help="Résultat net du trade"
                )

            submitted = st.form_submit_button("✅ Add Trade", use_container_width=True)

            if submitted:
                success = add_trade(
                    trade_date.strftime("%Y-%m-%d"),
                    trade_pair,
                    trade_direction,
                    trade_entry,
                    trade_exit,
                    trade_lots,
                    trade_result
                )
                if success:
                    st.success("✅ Trade ajouté avec succès dans Supabase!")
                    st.rerun()

# ============================================
# TAB 3 : ANALYTICS
# ============================================
with tab3:
    st.markdown('<div class="section-header">📊 Performance Analytics</div>', unsafe_allow_html=True)

    trades_df = get_all_trades()

    if not trades_df.empty:
        kpis = calculate_kpis(trades_df)

        # KPIs Row 1
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

        with kpi_col1:
            st.metric(
                label="🎯 Winrate",
                value=f"{kpis['winrate']:.1f}%",
                delta=f"{kpis['total_trades']} trades"
            )

        with kpi_col2:
            st.metric(
                label="💰 Profit Factor",
                value=f"{kpis['profit_factor']:.2f}",
                delta="Good" if kpis['profit_factor'] >= 1.5 else "Improve"
            )

        with kpi_col3:
            st.metric(
                label="🟢 Biggest Win",
                value=f"+{kpis['biggest_win']:.2f} €",
                delta=None
            )

        with kpi_col4:
            st.metric(
                label="🔴 Biggest Loss",
                value=f"{kpis['biggest_loss']:.2f} €",
                delta=None
            )

        st.markdown("---")

        # Graphiques
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("### 📈 Equity Curve")

            trades_df_sorted = trades_df.sort_values('date')
            trades_df_sorted['cumulative'] = trades_df_sorted['result'].cumsum() + capital_reel

            fig_equity = go.Figure()

            fig_equity.add_trace(go.Scatter(
                x=trades_df_sorted['date'],
                y=trades_df_sorted['cumulative'],
                mode='lines+markers',
                name='Equity',
                line=dict(color='#00ff88', width=3),
                marker=dict(size=8, color='#00ff88'),
                fill='tozeroy',
                fillcolor='rgba(0, 255, 136, 0.1)'
            ))

            fig_equity.add_hline(
                y=capital_reel,
                line_dash="dash",
                line_color="white",
                opacity=0.5,
                annotation_text=f"Initial: {capital_reel:.2f} €"
            )

            fig_equity.update_layout(
                template="plotly_dark",
                plot_bgcolor='#0a0e27',
                paper_bgcolor='#0a0e27',
                height=400,
                xaxis_title="Date",
                yaxis_title="Capital (€)",
                hovermode='x unified',
                font=dict(size=12)
            )

            st.plotly_chart(fig_equity, use_container_width=True)

        with chart_col2:
            st.markdown("### 📊 Win/Loss Distribution")

            winning_count = len(trades_df[trades_df['result'] > 0])
            losing_count = len(trades_df[trades_df['result'] < 0])

            fig_pie = go.Figure(data=[go.Pie(
                labels=['Wins', 'Losses'],
                values=[winning_count, losing_count],
                marker=dict(colors=['#00ff88', '#ff4444']),
                hole=0.5,
                textinfo='label+percent',
                textfont=dict(size=14, color='white')
            )])

            fig_pie.update_layout(
                template="plotly_dark",
                plot_bgcolor='#0a0e27',
                paper_bgcolor='#0a0e27',
                height=400,
                showlegend=True,
                font=dict(size=12)
            )

            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")

        # Statistiques détaillées
        stats_col1, stats_col2, stats_col3 = st.columns(3)

        with stats_col1:
            total_pnl = trades_df['result'].sum()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total P&L</div>
                <div class="metric-value {'metric-value-success' if total_pnl >= 0 else 'metric-value-danger'}">
                    {'+' if total_pnl >= 0 else ''}{total_pnl:.2f} €
                </div>
            </div>
            """, unsafe_allow_html=True)

        with stats_col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Average Win</div>
                <div class="metric-value metric-value-success">+{kpis['avg_win']:.2f} €</div>
            </div>
            """, unsafe_allow_html=True)

        with stats_col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Average Loss</div>
                <div class="metric-value metric-value-danger">{kpis['avg_loss']:.2f} €</div>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.info("📭 Aucune donnée disponible. Ajoutez des trades pour voir vos analytics.")

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #8b92a7; padding: 20px; font-size: 14px;">'
    '🌊 TradeFlow | Professional Trading Intelligence | Powered by Supabase'
    '</div>',
    unsafe_allow_html=True
)
