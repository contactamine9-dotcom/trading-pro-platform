import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from supabase import create_client, Client
import bcrypt
import os
import time

# ============================================
# CONFIGURATION DE LA PAGE (EN PREMIER)
# ============================================
st.set_page_config(
    page_title="TradeFlow",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# COOKIE MANAGER - INITIALISATION AVEC CLÉ
# ============================================
try:
    import extra_streamlit_components as stx
    cookie_manager = stx.CookieManager(key="tradeflow_cookies")
except Exception:
    cookie_manager = None

# ============================================
# CSS ULTRA-PRO FINTECH DARK MODE
# ============================================
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}

    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }

    [data-testid="stImage"] img {
        pointer-events: none !important;
        cursor: default !important;
    }

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div,
    .stDateInput > div > div > input {
        border-radius: 8px !important;
        background-color: #1e2130 !important;
        border: 1px solid #2d3142 !important;
        color: #fafafa !important;
    }

    .stButton > button {
        border-radius: 8px !important;
        background: linear-gradient(135deg, #00c9ff 0%, #92fe9d 100%) !important;
        color: #0e1117 !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 12px 24px !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(0, 201, 255, 0.4) !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #00c9ff !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 14px !important;
        color: #8b92a7 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #1e2130;
        border-radius: 8px;
        padding: 12px 24px;
        color: #8b92a7;
        border: 1px solid #2d3142;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00c9ff 0%, #92fe9d 100%);
        color: #0e1117 !important;
        font-weight: 700;
    }

    [data-testid="stDataFrame"] {
        border-radius: 8px;
        border: 1px solid #2d3142;
    }

    [data-testid="stForm"] {
        background-color: #1a1d29;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #2d3142;
    }

    .stAlert {
        border-radius: 8px;
        border-left: 4px solid #00c9ff;
    }

    .login-container {
        max-width: 450px;
        margin: 0 auto;
        padding: 40px 20px;
    }

    div[data-testid="stHorizontalBlock"] {
        gap: 16px;
    }
    </style>
""", unsafe_allow_html=True)

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
# AUTO-LOGIN VIA COOKIE (AU DÉBUT DU SCRIPT)
# ============================================
if cookie_manager and not st.session_state.authenticated:
    try:
        saved_email = cookie_manager.get("tradeflow_user_email")
        if saved_email:
            response = supabase.table('users').select("*").eq('email', saved_email).execute()
            if response.data:
                user = response.data[0]
                st.session_state.authenticated = True
                st.session_state.user_email = user['email']
                st.session_state.user_name = user.get('full_name', user['email'].split('@')[0])
    except:
        pass

# ============================================
# PAGE DE LOGIN
# ============================================
if not st.session_state.authenticated:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("logo1.png", width=300)
        except:
            st.markdown("# 🌊 TradeFlow")

        st.markdown("<h3 style='text-align: center; color: #8b92a7;'>Professional Trading Intelligence</h3>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")

    tab_login, tab_signup = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="votre@email.com")
            password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
            remember = st.checkbox("Se souvenir de moi", value=True)
            submit = st.form_submit_button("Se connecter", use_container_width=True)

            if submit and email and password:
                user = authenticate_user(email, password)
                if user:
                    # 1. Écrire le cookie
                    if remember and cookie_manager:
                        try:
                            cookie_manager.set("tradeflow_user_email", user['email'], expires_at=datetime(2025, 12, 31))
                        except:
                            pass

                    # 2. Attendre 1 seconde
                    time.sleep(1)

                    # 3. Forcer session_state
                    st.session_state.authenticated = True
                    st.session_state.user_email = user['email']
                    st.session_state.user_name = user.get('full_name', email.split('@')[0])

                    # 4. Rerun
                    st.rerun()
                else:
                    st.error("❌ Email ou mot de passe incorrect")

    with tab_signup:
        with st.form("signup_form"):
            new_email = st.text_input("Email", placeholder="votre@email.com")
            new_name = st.text_input("Nom complet", placeholder="Jean Dupont")
            new_password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
            new_password_confirm = st.text_input("Confirmer mot de passe", type="password", placeholder="••••••••")
            signup_submit = st.form_submit_button("Créer un compte", use_container_width=True)

            if signup_submit and new_email and new_password:
                if new_password != new_password_confirm:
                    st.error("❌ Les mots de passe ne correspondent pas")
                elif len(new_password) < 6:
                    st.error("❌ Mot de passe trop court (min 6 caractères)")
                else:
                    if create_user(new_email, new_password, new_name):
                        st.success("✅ Compte créé! Connectez-vous maintenant.")

    st.stop()

# ============================================
# APPLICATION PRINCIPALE
# ============================================

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown(f"**👤 {st.session_state.user_name}**")

with col2:
    try:
        st.image("logo1.png", width=300)
    except:
        st.markdown("<h1 style='text-align: center;'>🌊 TradeFlow</h1>", unsafe_allow_html=True)

with col3:
    if st.button("🚪 Déconnexion"):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.user_name = None

        if cookie_manager:
            try:
                cookie_manager.delete("tradeflow_user_email")
            except:
                pass

        st.rerun()

st.markdown("---")

capital_total = st.session_state.capital_reel + st.session_state.credit_broker

# ============================================
# TABS NAVIGATION (4 TABS)
# ============================================
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Dashboard", "⚡ Position", "📖 Journal", "📊 Analytics"])

# ============================================
# TAB 1: DASHBOARD
# ============================================
with tab1:
    st.markdown("### 💎 Votre Capital")

    col_input1, col_input2 = st.columns(2)
    with col_input1:
        capital_reel = st.number_input(
            "💰 Capital Réel (€)",
            min_value=0.0,
            value=st.session_state.capital_reel,
            step=50.0,
            key="capital_input"
        )
        st.session_state.capital_reel = capital_reel

    with col_input2:
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

    trades_df = get_user_trades(st.session_state.user_email)

    if not trades_df.empty:
        kpis = calculate_kpis(trades_df)

        st.markdown("### 📈 Performance Globale")

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

        st.markdown("### 📈 Equity Curve")
        trades_df_sorted = trades_df.sort_values('date')
        trades_df_sorted['cumulative'] = trades_df_sorted['result'].cumsum() + capital_reel

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trades_df_sorted['date'],
            y=trades_df_sorted['cumulative'],
            mode='lines+markers',
            name='Equity',
            line=dict(color='#00c9ff', width=3),
            marker=dict(size=6, color='#92fe9d')
        ))

        fig.update_layout(
            template="plotly_dark",
            height=400,
            xaxis_title="Date",
            yaxis_title="Capital (€)",
            hovermode='x unified',
            plot_bgcolor='#0e1117',
            paper_bgcolor='#0e1117'
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
            elif risk_reward >= 2:
                st.success("✅ Excellent Risk:Reward ratio!")

# ============================================
# TAB 3: JOURNAL DE TRADING
# ============================================
with tab3:
    st.markdown("### 📖 Journal de Trading")

    trades_df = get_user_trades(st.session_state.user_email)

    if not trades_df.empty:
        st.markdown("#### 📜 Historique des Trades")

        display_df = trades_df[['date', 'pair', 'direction', 'entry_price', 'exit_price', 'lots', 'result']].copy()
        display_df['result'] = display_df['result'].apply(lambda x: f"{'+' if x > 0 else ''}{x:.2f} €")
        display_df.columns = ['Date', 'Asset', 'Direction', 'Entry', 'Exit', 'Lots', 'P&L']

        st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)

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
                # 1. Envoyer à Supabase
                try:
                    response = supabase.table('trades').insert({
                        "user_email": st.session_state.user_email,
                        "date": trade_date.strftime("%Y-%m-%d"),
                        "pair": trade_pair,
                        "direction": trade_direction,
                        "entry_price": trade_entry,
                        "exit_price": trade_exit,
                        "lots": trade_lots,
                        "result": trade_result,
                        "timestamp": datetime.now().isoformat()
                    }).execute()

                    # 2. Vérifier si response.data existe
                    if response.data:
                        st.success("✅ Trade sauvegardé !")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Erreur d'enregistrement Supabase")
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")
            else:
                st.error("❌ Veuillez remplir Entry Price et Exit Price")

# ============================================
# TAB 4: ANALYTICS
# ============================================
with tab4:
    st.markdown("### 📊 Analytics & Statistiques Avancées")

    trades_df = get_user_trades(st.session_state.user_email)

    if not trades_df.empty:
        kpis = calculate_kpis(trades_df)

        st.markdown("#### 🎯 KPIs Détaillés")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🏆 Biggest Win", f"+{kpis['biggest_win']:.2f} €")
        with col2:
            st.metric("💥 Biggest Loss", f"{kpis['biggest_loss']:.2f} €")
        with col3:
            st.metric("📈 Avg Win", f"+{kpis['avg_win']:.2f} €")
        with col4:
            st.metric("📉 Avg Loss", f"{kpis['avg_loss']:.2f} €")

        st.markdown("---")

        st.markdown("#### 🌍 Distribution par Asset")

        asset_counts = trades_df['pair'].value_counts()

        fig_assets = go.Figure(data=[go.Pie(
            labels=asset_counts.index,
            values=asset_counts.values,
            hole=0.4,
            marker=dict(colors=['#00c9ff', '#92fe9d', '#ff6b6b', '#ffd93d', '#a29bfe', '#fd79a8'])
        )])

        fig_assets.update_layout(
            template="plotly_dark",
            height=400,
            plot_bgcolor='#0e1117',
            paper_bgcolor='#0e1117'
        )

        st.plotly_chart(fig_assets, use_container_width=True)

        st.markdown("---")

        st.markdown("#### 🔄 Performance Long vs Short")

        col1, col2 = st.columns(2)

        with col1:
            long_trades = trades_df[trades_df['direction'] == 'Long']
            if not long_trades.empty:
                long_pnl = long_trades['result'].sum()
                long_winrate = (len(long_trades[long_trades['result'] > 0]) / len(long_trades)) * 100
                st.metric("📈 Long P&L", f"{long_pnl:+.2f} €")
                st.metric("🎯 Long Winrate", f"{long_winrate:.1f}%")
            else:
                st.info("Aucun trade Long")

        with col2:
            short_trades = trades_df[trades_df['direction'] == 'Short']
            if not short_trades.empty:
                short_pnl = short_trades['result'].sum()
                short_winrate = (len(short_trades[short_trades['result'] > 0]) / len(short_trades)) * 100
                st.metric("📉 Short P&L", f"{short_pnl:+.2f} €")
                st.metric("🎯 Short Winrate", f"{short_winrate:.1f}%")
            else:
                st.info("Aucun trade Short")

        st.markdown("---")

        st.markdown("#### 📊 Distribution des Résultats")

        fig_dist = go.Figure()

        fig_dist.add_trace(go.Histogram(
            x=trades_df['result'],
            nbinsx=20,
            marker=dict(
                color=trades_df['result'],
                colorscale=[[0, '#ff6b6b'], [0.5, '#ffd93d'], [1, '#92fe9d']],
                line=dict(color='#0e1117', width=1)
            )
        ))

        fig_dist.update_layout(
            template="plotly_dark",
            height=400,
            xaxis_title="P&L (€)",
            yaxis_title="Nombre de trades",
            plot_bgcolor='#0e1117',
            paper_bgcolor='#0e1117'
        )

        st.plotly_chart(fig_dist, use_container_width=True)

    else:
        st.info("📭 Aucune donnée pour l'analyse. Ajoutez des trades dans le Journal!")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #8b92a7; font-size: 12px;'>🌊 TradeFlow | Professional Trading Intelligence | Powered by Supabase</p>", unsafe_allow_html=True)
