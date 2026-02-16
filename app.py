import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client
import bcrypt
import os

# ============================================
# CONFIGURATION
# ============================================
st.set_page_config(
    page_title="TradeFlow",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Simple
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Configuration des actifs
ASSET_CONFIG = {
    "XAUUSD": {"name": "Gold", "point_value": 100.0, "currency": "$"},
    "DJ30": {"name": "Dow Jones 30", "point_value": 5.0, "currency": "$"},
    "DAX40": {"name": "DAX 40", "point_value": 25.0, "currency": "€"},
    "NAS100": {"name": "Nasdaq 100", "point_value": 20.0, "currency": "$"},
    "BTCUSD": {"name": "Bitcoin", "point_value": 1.0, "currency": "$"},
    "ETHUSD": {"name": "Ethereum", "point_value": 1.0, "currency": "$"}
}

# ============================================
# CONNEXION SUPABASE
# ============================================
@st.cache_resource
def init_supabase():
    try:
        supabase_url = os.getenv("SUPABASE_URL") or st.secrets["supabase"]["url"]
        supabase_key = os.getenv("SUPABASE_KEY") or st.secrets["supabase"]["key"]
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        st.error(f"❌ Erreur Supabase: {str(e)}")
        st.stop()

supabase = init_supabase()

# ============================================
# FONCTIONS AUTH
# ============================================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def authenticate_user(email: str, password: str):
    try:
        response = supabase.table('users').select("*").eq('email', email).execute()
        if not response.data:
            return None
        user = response.data[0]
        if verify_password(password, user['password_hash']):
            return user
        return None
    except:
        return None

def create_user(email: str, password: str, full_name: str = None):
    try:
        password_hash = hash_password(password)
        data = {"email": email, "password_hash": password_hash, "full_name": full_name}
        supabase.table('users').insert(data).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
        return False

# ============================================
# FONCTIONS TRADES
# ============================================
def add_trade(user_email, date, pair, direction, entry_price, exit_price, lots, result):
    try:
        data = {
            "user_email": user_email,
            "date": date,
            "pair": pair,
            "direction": direction,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "lots": lots,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        supabase.table('trades').insert(data).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
        return False

def get_user_trades(user_email):
    try:
        response = supabase.table('trades').select("*").eq('user_email', user_email).order('date', desc=True).execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def delete_user_trades(user_email):
    try:
        response = supabase.table('trades').select("id").eq('user_email', user_email).execute()
        if response.data:
            for trade in response.data:
                supabase.table('trades').delete().eq('id', trade['id']).execute()
        return True
    except:
        return False

def calculate_kpis(trades_df):
    if trades_df.empty:
        return {'winrate': 0, 'profit_factor': 0, 'biggest_win': 0, 'biggest_loss': 0,
                'total_trades': 0, 'avg_win': 0, 'avg_loss': 0}

    winning_trades = trades_df[trades_df['result'] > 0]
    losing_trades = trades_df[trades_df['result'] < 0]
    total_wins = winning_trades['result'].sum() if not winning_trades.empty else 0
    total_losses = abs(losing_trades['result'].sum()) if not losing_trades.empty else 0
    winrate = (len(winning_trades) / len(trades_df)) * 100 if len(trades_df) > 0 else 0
    profit_factor = total_wins / total_losses if total_losses > 0 else (total_wins if total_wins > 0 else 0)

    return {
        'winrate': winrate,
        'profit_factor': profit_factor,
        'biggest_win': trades_df['result'].max() if not trades_df.empty else 0,
        'biggest_loss': trades_df['result'].min() if not trades_df.empty else 0,
        'total_trades': len(trades_df),
        'avg_win': winning_trades['result'].mean() if not winning_trades.empty else 0,
        'avg_loss': losing_trades['result'].mean() if not losing_trades.empty else 0
    }

# ============================================
# SESSION STATE
# ============================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'capital_reel' not in st.session_state:
    st.session_state.capital_reel = 733.18
if 'credit_broker' not in st.session_state:
    st.session_state.credit_broker = 500.0

# ============================================
# PAGE DE LOGIN
# ============================================
if not st.session_state.authenticated:
    st.markdown("# 🌊 TradeFlow")
    st.markdown("### Professional Trading Intelligence")
    st.markdown("---")

    tab_login, tab_signup = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Mot de passe", type="password")
            submit = st.form_submit_button("Se connecter", use_container_width=True)

            if submit and email and password:
                user = authenticate_user(email, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user_email = user['email']
                    st.session_state.user_name = user.get('full_name', email.split('@')[0])
                    st.rerun()
                else:
                    st.error("❌ Email ou mot de passe incorrect")

    with tab_signup:
        with st.form("signup_form"):
            new_email = st.text_input("Email")
            new_name = st.text_input("Nom complet")
            new_password = st.text_input("Mot de passe", type="password")
            new_password_confirm = st.text_input("Confirmer mot de passe", type="password")
            signup_submit = st.form_submit_button("Créer un compte", use_container_width=True)

            if signup_submit and new_email and new_password:
                if new_password != new_password_confirm:
                    st.error("❌ Les mots de passe ne correspondent pas")
                elif len(new_password) < 6:
                    st.error("❌ Mot de passe trop court (min 6 caractères)")
                else:
                    if create_user(new_email, new_password, new_name):
                        st.success("✅ Compte créé! Connectez-vous.")

    st.stop()

# ============================================
# APPLICATION PRINCIPALE
# ============================================

# Header avec logo
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown(f"**👤 {st.session_state.user_name}**")

with col2:
    # Logo simple centré
    try:
        st.image("logo1.png", width=300)
    except:
        st.markdown("# 🌊 TradeFlow")

with col3:
    if st.button("🚪 Déconnexion"):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.user_name = None
        st.rerun()

st.markdown("---")

# Calcul du capital
capital_total = st.session_state.capital_reel + st.session_state.credit_broker

# ============================================
# TABS NAVIGATION
# ============================================
tab1, tab2, tab3 = st.tabs(["🏠 Dashboard", "⚡ Position", "📖 Journal"])

# ============================================
# TAB 1: DASHBOARD
# ============================================
with tab1:
    st.markdown("### 💎 Votre Capital")

    col_cap1, col_cap2 = st.columns(2)
    with col_cap1:
        capital_reel = st.number_input(
            "💰 Capital Réel (€)",
            min_value=0.0,
            value=st.session_state.capital_reel,
            step=50.0,
            key="capital_input"
        )
        st.session_state.capital_reel = capital_reel

    with col_cap2:
        credit_broker = st.number_input(
            "🏦 Crédit Broker (€)",
            min_value=0.0,
            value=st.session_state.credit_broker,
            step=50.0,
            key="credit_input"
        )
        st.session_state.credit_broker = credit_broker

    capital_total = capital_reel + credit_broker

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Capital Réel", f"{capital_reel:.2f} €")
    with col2:
        st.metric("🏦 Crédit Broker", f"{credit_broker:.2f} €")
    with col3:
        st.metric("💎 Total Equity", f"{capital_total:.2f} €")

    st.markdown("---")

    # Performance
    trades_df = get_user_trades(st.session_state.user_email)

    if not trades_df.empty:
        kpis = calculate_kpis(trades_df)

        st.markdown("### 📈 Performance")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Winrate", f"{kpis['winrate']:.1f}%")
        with col2:
            st.metric("💰 Profit Factor", f"{kpis['profit_factor']:.2f}")
        with col3:
            total_pnl = trades_df['result'].sum()
            st.metric("💵 Total P&L", f"{total_pnl:+.2f} €")
        with col4:
            st.metric("📊 Total Trades", f"{kpis['total_trades']}")

        # Equity Curve
        st.markdown("### 📈 Equity Curve")
        trades_df_sorted = trades_df.sort_values('date')
        trades_df_sorted['cumulative'] = trades_df_sorted['result'].cumsum() + capital_reel

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trades_df_sorted['date'],
            y=trades_df_sorted['cumulative'],
            mode='lines+markers',
            line=dict(color='#00c9ff', width=3)
        ))

        fig.update_layout(
            template="plotly_dark",
            height=400,
            xaxis_title="Date",
            yaxis_title="Capital (€)"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 Aucune donnée. Ajoutez des trades dans le Journal!")

# ============================================
# TAB 2: CALCULATEUR DE POSITION
# ============================================
with tab2:
    st.markdown("### ⚡ Calculateur de Position")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Paramètres")

        selected_pair = st.selectbox(
            "Asset",
            options=list(ASSET_CONFIG.keys()),
            format_func=lambda x: f"{x} - {ASSET_CONFIG[x]['name']}"
        )

        asset_info = ASSET_CONFIG[selected_pair]

        entry_price = st.number_input("Entry Price", min_value=0.0, value=2000.0 if "XAU" in selected_pair else 1.1000, step=0.01, format="%.4f")
        stop_loss = st.number_input("Stop Loss", min_value=0.0, value=1950.0 if "XAU" in selected_pair else 1.0950, step=0.01, format="%.4f")
        take_profit = st.number_input("Take Profit", min_value=0.0, value=2100.0 if "XAU" in selected_pair else 1.1100, step=0.01, format="%.4f")

        risque_pct = st.slider("🎯 Risque par Trade (%)", min_value=0.5, max_value=10.0, value=2.0, step=0.5)
        montant_risque = capital_total * (risque_pct / 100)

        st.info(f"💰 Montant à risquer : **{montant_risque:.2f} €**")

        point_value = st.number_input(f"Point Value ({asset_info['currency']})", min_value=0.01, value=asset_info['point_value'], step=1.0)

    with col_right:
        st.markdown("#### Résultats")

        if entry_price > 0 and stop_loss > 0 and take_profit > 0 and point_value > 0:
            risk_distance = abs(entry_price - stop_loss)
            reward_distance = abs(take_profit - entry_price)

            if risk_distance > 0:
                position_size = montant_risque / (risk_distance * point_value)
            else:
                position_size = 0

            perte_max = risk_distance * point_value * position_size
            gain_potentiel = reward_distance * point_value * position_size
            risk_reward = reward_distance / risk_distance if risk_distance > 0 else 0

            st.metric("📏 Position Size", f"{position_size:.4f} lots")
            st.metric("🔴 Max Loss", f"-{perte_max:.2f} €")
            st.metric("🟢 Potential Gain", f"+{gain_potentiel:.2f} €")
            st.metric("⚖️ Risk:Reward", f"1:{risk_reward:.2f}")

            if risque_pct > 5:
                st.error("🚨 RISQUE ÉLEVÉ : Plus de 5% du capital !")

# ============================================
# TAB 3: JOURNAL DE TRADING
# ============================================
with tab3:
    st.markdown("### 📖 Journal de Trading")

    # Récupérer les trades (à chaque affichage du tab)
    trades_df = get_user_trades(st.session_state.user_email)

    # Afficher le tableau
    if not trades_df.empty:
        st.markdown("#### 📜 Historique")

        display_df = trades_df[['date', 'pair', 'direction', 'entry_price', 'exit_price', 'lots', 'result']].copy()
        display_df['result'] = display_df['result'].apply(lambda x: f"{'+' if x > 0 else ''}{x:.2f} €")
        display_df.columns = ['Date', 'Asset', 'Direction', 'Entry', 'Exit', 'Lots', 'P&L']

        st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)

        # Actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Supprimer tous les trades"):
                if delete_user_trades(st.session_state.user_email):
                    st.success("✅ Trades supprimés")
                    st.rerun()
        with col2:
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export CSV", data=csv, file_name=f"trades_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
    else:
        st.info("📭 Aucun trade enregistré")

    st.markdown("---")

    # Formulaire d'ajout
    st.markdown("#### ➕ Ajouter un Trade")

    with st.form("add_trade_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            trade_date = st.date_input("Date", datetime.now())
            trade_pair = st.selectbox("Asset", list(ASSET_CONFIG.keys()))
            trade_direction = st.radio("Direction", ["Long", "Short"], horizontal=True)
            trade_entry = st.number_input("Entry Price", min_value=0.0, value=0.0, step=0.01, format="%.4f")

        with col2:
            trade_exit = st.number_input("Exit Price", min_value=0.0, value=0.0, step=0.01, format="%.4f")
            trade_lots = st.number_input("Lots", min_value=0.0001, value=0.01, step=0.01, format="%.4f")
            trade_result = st.number_input("P&L (€)", value=0.0, step=10.0)

        submitted = st.form_submit_button("✅ Ajouter le Trade", use_container_width=True)

        if submitted:
            if trade_entry > 0 and trade_exit > 0:
                success = add_trade(
                    st.session_state.user_email,
                    trade_date.strftime("%Y-%m-%d"),
                    trade_pair,
                    trade_direction,
                    trade_entry,
                    trade_exit,
                    trade_lots,
                    trade_result
                )
                if success:
                    st.success("✅ Trade ajouté avec succès !")
                    # PAS de st.rerun() - l'utilisateur reste sur le Journal
                    # Le prochain refresh du tab affichera le nouveau trade
            else:
                st.error("❌ Veuillez remplir Entry Price et Exit Price")
