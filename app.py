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
# COOKIE MANAGER - INITIALISATION ROBUSTE
# ============================================
try:
    import extra_streamlit_components as stx
    cookie_manager = stx.CookieManager()
except:
    # Fallback si problème d'import
    cookie_manager = None

# ============================================
# CSS ULTRA-PRO FINTECH DARK MODE
# ============================================
st.markdown("""
    <style>
    /* Cacher tous les éléments Streamlit pour un look application native */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Theme Fintech Dark Mode */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }

    /* Logo non-cliquable (pas de zoom) */
    [data-testid="stImage"] img {
        pointer-events: none;
        cursor: default;
    }

    /* Inputs et boutons arrondis */
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

    /* Métriques stylisées */
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

    /* Tabs modernes */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #1a1d29;
        border-radius: 8px;
        padding: 12px 24px;
        color: #8b92a7;
        font-weight: 600;
        border: 1px solid #2d3142;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00c9ff 0%, #92fe9d 100%);
        color: #0e1117;
        border: none;
    }

    /* DataFrames */
    .dataframe {
        border-radius: 8px !important;
        border: 1px solid #2d3142 !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1a1d29 !important;
        border-radius: 8px !important;
        border: 1px solid #2d3142 !important;
        color: #fafafa !important;
    }

    /* Login page styles */
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 40px;
        background: linear-gradient(135deg, #1a1d29 0%, #12141d 100%);
        border-radius: 16px;
        border: 1px solid #2d3142;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }

    .login-header {
        text-align: center;
        color: #00c9ff;
        font-size: 36px;
        font-weight: 900;
        margin-bottom: 10px;
    }

    .login-subtitle {
        text-align: center;
        color: #8b92a7;
        font-size: 14px;
        margin-bottom: 30px;
    }

    /* Danger alert animation */
    @keyframes pulse-red {
        0%, 100% {
            background-color: rgba(255, 68, 68, 0.1);
            border-color: #ff4444;
        }
        50% {
            background-color: rgba(255, 68, 68, 0.3);
            border-color: #ff0000;
        }
    }

    .danger-alert {
        animation: pulse-red 2s infinite;
        background-color: rgba(255, 68, 68, 0.1);
        border: 2px solid #ff4444;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
    }

    /* Card style */
    .metric-card {
        background: linear-gradient(135deg, #1a1d29 0%, #12141d 100%);
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #2d3142;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        text-align: center;
        margin: 10px 0;
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
        color: #00c9ff;
        font-size: 32px;
        font-weight: 700;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Configuration des actifs
ASSET_CONFIG = {
    "XAUUSD": {"name": "Gold", "point_value": 100.0, "currency": "$", "description": "1 point = 100$ par lot standard"},
    "DJ30": {"name": "Dow Jones 30", "point_value": 5.0, "currency": "$", "description": "1 point = 5$ par lot"},
    "DAX40": {"name": "DAX 40", "point_value": 25.0, "currency": "€", "description": "1 point = 25€ par lot"},
    "NAS100": {"name": "Nasdaq 100", "point_value": 20.0, "currency": "$", "description": "1 point = 20$ par lot"},
    "BTCUSD": {"name": "Bitcoin", "point_value": 1.0, "currency": "$", "description": "1$ move = 1$ PnL"},
    "ETHUSD": {"name": "Ethereum", "point_value": 1.0, "currency": "$", "description": "1$ move = 1$ PnL"}
}

# ============================================
# CONNEXION SUPABASE
# ============================================
@st.cache_resource
def init_supabase():
    """Initialise la connexion Supabase"""
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            if "supabase" not in st.secrets:
                st.error("❌ Configuration Supabase manquante")
                st.stop()
            supabase_url = st.secrets["supabase"]["url"]
            supabase_key = st.secrets["supabase"]["key"]

        supabase: Client = create_client(supabase_url, supabase_key)
        return supabase
    except Exception as e:
        st.error(f"❌ Erreur de connexion à Supabase: {str(e)}")
        st.stop()

supabase = init_supabase()

# ============================================
# FONCTIONS D'AUTHENTIFICATION
# ============================================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_user(email: str, password: str, full_name: str = None):
    try:
        password_hash = hash_password(password)
        data = {"email": email, "password_hash": password_hash, "full_name": full_name}
        supabase.table('users').insert(data).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
        return False

def authenticate_user(email: str, password: str):
    try:
        response = supabase.table('users').select("*").eq('email', email).execute()
        if not response.data:
            return None
        user = response.data[0]
        if verify_password(password, user['password_hash']):
            return user
        return None
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
        return None

def get_user_by_email(email: str):
    """Récupère un utilisateur par email (pour auto-login via cookie)"""
    try:
        response = supabase.table('users').select("*").eq('email', email).execute()
        if response.data:
            return response.data[0]
        return None
    except:
        return None

def check_table_exists(table_name: str):
    try:
        supabase.table(table_name).select("id").limit(1).execute()
        return True
    except:
        return False

# ============================================
# FONCTIONS TRADES
# ============================================
def add_trade(user_email, date, pair, direction, entry_price, exit_price, lots, result):
    try:
        data = {
            "user_email": user_email, "date": date, "pair": pair, "direction": direction,
            "entry_price": entry_price, "exit_price": exit_price, "lots": lots,
            "result": result, "timestamp": datetime.now().isoformat()
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
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
        return pd.DataFrame()

def delete_user_trades(user_email):
    try:
        response = supabase.table('trades').select("id").eq('user_email', user_email).execute()
        if response.data:
            for trade in response.data:
                supabase.table('trades').delete().eq('id', trade['id']).execute()
        return True
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
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
        'winrate': winrate, 'profit_factor': profit_factor,
        'biggest_win': trades_df['result'].max() if not trades_df.empty else 0,
        'biggest_loss': trades_df['result'].min() if not trades_df.empty else 0,
        'total_trades': len(trades_df),
        'avg_win': winning_trades['result'].mean() if not winning_trades.empty else 0,
        'avg_loss': losing_trades['result'].mean() if not losing_trades.empty else 0
    }

# ============================================
# SESSION STATE INITIALIZATION
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
# AUTO-LOGIN VIA COOKIE (ROBUSTE)
# ============================================
if not st.session_state.authenticated and cookie_manager is not None:
    try:
        # Récupérer les cookies de manière sécurisée
        cookies = cookie_manager.get_all()

        if cookies and 'user_email' in cookies:
            user_email_cookie = cookies.get('user_email')
            user_name_cookie = cookies.get('user_name', '')

            if user_email_cookie:
                # Vérifier que l'utilisateur existe toujours
                user = get_user_by_email(user_email_cookie)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user_email = user_email_cookie
                    st.session_state.user_name = user_name_cookie if user_name_cookie else user.get('full_name', user_email_cookie.split('@')[0])
    except:
        # Si erreur lors de la lecture des cookies, continuer sans auto-login
        pass

# ============================================
# PAGE DE LOGIN
# ============================================
def show_login_page():
    if not check_table_exists('users'):
        st.error("""
        ⚠️ **Table 'users' non trouvée**

        Veuillez exécuter le fichier `create_users_table.sql` dans Supabase SQL Editor.
        """)
        st.stop()

    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-header">🌊 TradeFlow</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Professional Trading Intelligence</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="votre@email.com")
            password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
            remember_me = st.checkbox("Se souvenir de moi (30 jours)", value=True)
            submit = st.form_submit_button("Se connecter", use_container_width=True)

            if submit:
                if email and password:
                    user = authenticate_user(email, password)
                    if user:
                        # Authentification réussie
                        st.session_state.authenticated = True
                        st.session_state.user_email = user['email']
                        st.session_state.user_name = user.get('full_name', email.split('@')[0])

                        # Créer les cookies si demandé
                        if remember_me and cookie_manager is not None:
                            try:
                                cookie_manager.set(
                                    cookie="user_email",
                                    val=user['email'],
                                    expires_at=datetime.now() + pd.Timedelta(days=30)
                                )
                                cookie_manager.set(
                                    cookie="user_name",
                                    val=st.session_state.user_name,
                                    expires_at=datetime.now() + pd.Timedelta(days=30)
                                )
                                # Petit délai pour laisser les cookies s'écrire
                                time.sleep(0.5)
                            except:
                                pass

                        st.success("✅ Connexion réussie!")
                        time.sleep(0.5)  # Délai avant rerun
                        st.rerun()
                    else:
                        st.error("❌ Email ou mot de passe incorrect")
                else:
                    st.warning("⚠️ Veuillez remplir tous les champs")

    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("Email", placeholder="votre@email.com", key="signup_email")
            new_name = st.text_input("Nom complet", placeholder="John Doe", key="signup_name")
            new_password = st.text_input("Mot de passe", type="password", placeholder="••••••••", key="signup_password")
            new_password_confirm = st.text_input("Confirmer mot de passe", type="password", placeholder="••••••••")
            signup_submit = st.form_submit_button("Créer un compte", use_container_width=True)

            if signup_submit:
                if new_email and new_password and new_password_confirm:
                    if new_password != new_password_confirm:
                        st.error("❌ Les mots de passe ne correspondent pas")
                    elif len(new_password) < 6:
                        st.error("❌ Le mot de passe doit contenir au moins 6 caractères")
                    else:
                        if create_user(new_email, new_password, new_name):
                            st.success("✅ Compte créé! Connectez-vous maintenant.")
                else:
                    st.warning("⚠️ Veuillez remplir tous les champs")

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# MAIN APP
# ============================================
def show_main_app():
    # Header avec logo centré et déconnexion
    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_left:
        st.markdown(f'<p style="color: #8b92a7; margin-top: 20px;">👤 {st.session_state.user_name}</p>', unsafe_allow_html=True)

    with col_center:
        # Logo centré (non-cliquable grâce au CSS)
        try:
            st.image("logo1.png", width=350)
        except:
            st.markdown('<h1 style="color: #00c9ff; text-align: center;">🌊 TradeFlow</h1>', unsafe_allow_html=True)

    with col_right:
        if st.button("🚪 Déconnexion", use_container_width=True):
            # Supprimer les cookies
            if cookie_manager is not None:
                try:
                    cookie_manager.delete(cookie="user_email")
                    cookie_manager.delete(cookie="user_name")
                except:
                    pass

            # Réinitialiser la session
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.session_state.user_name = None
            st.rerun()

    st.markdown("---")

    # ============================================
    # TABS NAVIGATION
    # ============================================
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 DASHBOARD", "⚡ CALCULATEUR", "📖 JOURNAL", "📊 ANALYTICS"])

    # Calcul du capital total (utilisé dans plusieurs tabs)
    capital_total = st.session_state.capital_reel + st.session_state.credit_broker

    # ============================================
    # TAB 1: DASHBOARD
    # ============================================
    with tab1:
        st.markdown("### 💎 Votre Capital")

        # Inputs modifiables pour Capital et Crédit
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

        st.markdown("<br>", unsafe_allow_html=True)

        # Métriques principales
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("💰 Capital Réel", f"{capital_reel:.2f} €")

        with col2:
            st.metric("🏦 Crédit Broker", f"{credit_broker:.2f} €")

        with col3:
            st.metric("💎 Total Equity", f"{capital_total:.2f} €")

        st.markdown("<br>", unsafe_allow_html=True)

        # Performance Overview
        trades_df = get_user_trades(st.session_state.user_email)

        if not trades_df.empty:
            kpis = calculate_kpis(trades_df)

            st.markdown("### 📈 Performance Overview")

            kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

            with kpi_col1:
                st.metric("🎯 Winrate", f"{kpis['winrate']:.1f}%")

            with kpi_col2:
                st.metric("💰 Profit Factor", f"{kpis['profit_factor']:.2f}")

            with kpi_col3:
                total_pnl = trades_df['result'].sum()
                st.metric("💵 Total P&L", f"{total_pnl:+.2f} €")

            with kpi_col4:
                st.metric("📊 Total Trades", f"{kpis['total_trades']}")

            st.markdown("<br>", unsafe_allow_html=True)

            # Quick equity curve
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
                fill='tozeroy',
                fillcolor='rgba(0, 201, 255, 0.1)'
            ))

            fig.add_hline(y=capital_reel, line_dash="dash", line_color="white", opacity=0.3)

            fig.update_layout(
                template="plotly_dark",
                plot_bgcolor='#0e1117',
                paper_bgcolor='#0e1117',
                height=400,
                xaxis_title="Date",
                yaxis_title="Capital (€)",
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 Aucune donnée de trading. Ajoutez des trades dans le Journal!")

    # ============================================
    # TAB 2: CALCULATEUR
    # ============================================
    with tab2:
        st.markdown("### ⚡ Calculateur de Position Size")

        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            st.markdown("#### 🎲 Paramètres du Trade")

            # Sélection de l'actif
            selected_pair = st.selectbox(
                "Asset",
                options=list(ASSET_CONFIG.keys()),
                format_func=lambda x: f"{x} - {ASSET_CONFIG[x]['name']}"
            )

            asset_info = ASSET_CONFIG[selected_pair]
            st.info(f"📌 {asset_info['description']}")

            # Prix d'entrée
            entry_price = st.number_input(
                "Entry Price",
                min_value=0.0,
                value=2000.0 if "XAU" in selected_pair else 1.1000,
                step=0.01,
                format="%.4f"
            )

            # Stop Loss
            stop_loss = st.number_input(
                "Stop Loss",
                min_value=0.0,
                value=1950.0 if "XAU" in selected_pair else 1.0950,
                step=0.01,
                format="%.4f"
            )

            # Take Profit
            take_profit = st.number_input(
                "Take Profit",
                min_value=0.0,
                value=2100.0 if "XAU" in selected_pair else 1.1100,
                step=0.01,
                format="%.4f"
            )

            # Risque %
            risque_pct = st.slider(
                "🎯 Risque par Trade (%)",
                min_value=0.5,
                max_value=10.0,
                value=2.0,
                step=0.5
            )

            montant_risque_total = capital_total * (risque_pct / 100)

            st.info(f"💰 Montant à risquer : **{montant_risque_total:.2f} €** ({risque_pct}% de {capital_total:.2f}€)")

            # Valeur du point (modifiable)
            st.markdown("---")
            st.markdown("#### ⚙️ Configuration")

            point_value = st.number_input(
                f"Point Value ({asset_info['currency']})",
                min_value=0.01,
                value=asset_info['point_value'],
                step=0.01 if asset_info['point_value'] < 10 else 1.0,
                help=f"Valeur prédéfinie: {asset_info['point_value']}{asset_info['currency']}"
            )

        with col_right:
            st.markdown("#### 📊 Résultats")

            if entry_price > 0 and stop_loss > 0 and take_profit > 0 and point_value > 0:
                # Calculs
                risk_distance = abs(entry_price - stop_loss)
                reward_distance = abs(take_profit - entry_price)

                if risk_distance > 0:
                    position_size_lots = montant_risque_total / (risk_distance * point_value)
                else:
                    position_size_lots = 0

                perte_max = risk_distance * point_value * position_size_lots
                gain_potentiel = reward_distance * point_value * position_size_lots
                risk_reward_ratio = reward_distance / risk_distance if risk_distance > 0 else 0

                # Affichage des métriques
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Position Size</div>
                    <div class="metric-value">{position_size_lots:.4f} lots</div>
                </div>
                """, unsafe_allow_html=True)

                metric_col1, metric_col2 = st.columns(2)

                with metric_col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Max Loss</div>
                        <div class="metric-value" style="color: #ff4444;">-{perte_max:.2f} €</div>
                        <small style="color: #8b92a7;">{risk_distance:.4f} points</small>
                    </div>
                    """, unsafe_allow_html=True)

                with metric_col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Potential Gain</div>
                        <div class="metric-value" style="color: #00ff88;">+{gain_potentiel:.2f} €</div>
                        <small style="color: #8b92a7;">{reward_distance:.4f} points</small>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Risk:Reward Ratio</div>
                    <div class="metric-value" style="color: {'#00ff88' if risk_reward_ratio >= 2 else '#ffaa00'};">1:{risk_reward_ratio:.2f}</div>
                </div>
                """, unsafe_allow_html=True)

                # Alerte risque élevé
                if risque_pct > 5 or perte_max > st.session_state.capital_reel:
                    st.markdown("<br>", unsafe_allow_html=True)
                    alert_messages = []
                    if risque_pct > 5:
                        alert_messages.append(f"⚠️ Risque de {risque_pct}% dépasse 5%")
                    if perte_max > st.session_state.capital_reel:
                        alert_messages.append(f"⚠️ Perte potentielle entamera le crédit broker")

                    st.markdown(f"""
                    <div class="danger-alert">
                        <h3 style="color: #ff4444; margin: 0;">🚨 ALERTE RISQUE ÉLEVÉ</h3>
                        <p style="color: #ffcccc; margin-top: 10px;">{'<br>'.join(alert_messages)}</p>
                    </div>
                    """, unsafe_allow_html=True)

                # Détails du calcul
                with st.expander("📋 Détails du Calcul"):
                    st.markdown(f"""
                    **Formule:**
                    ```
                    Position Size = Capital à Risquer / (Distance SL × Valeur Point)
                    Position Size = {montant_risque_total:.2f} / ({risk_distance:.4f} × {point_value})
                    Position Size = {position_size_lots:.4f} lots
                    ```

                    **Paramètres:**
                    - Capital Total: {capital_total:.2f} €
                    - Risque: {risque_pct}% = {montant_risque_total:.2f} €
                    - Distance SL: {risk_distance:.4f} points
                    - Distance TP: {reward_distance:.4f} points
                    - Valeur Point: {point_value} {asset_info['currency']}

                    **P&L:**
                    - Perte Max = {perte_max:.2f} €
                    - Gain Potentiel = {gain_potentiel:.2f} €
                    - Ratio R:R = 1:{risk_reward_ratio:.2f}
                    """)
            else:
                st.warning("⚠️ Veuillez remplir tous les champs")

    # ============================================
    # TAB 3: JOURNAL
    # ============================================
    with tab3:
        st.markdown("### 📖 Journal de Trading")

        trades_df = get_user_trades(st.session_state.user_email)

        # Afficher le tableau si des trades existent
        if not trades_df.empty:
            st.markdown("#### 📜 Historique des Trades")

            display_df = trades_df[['date', 'pair', 'direction', 'entry_price', 'exit_price', 'lots', 'result']].copy()
            display_df['result'] = display_df['result'].apply(lambda x: f"{'+' if x > 0 else ''}{x:.2f} €")
            display_df.columns = ['Date', 'Asset', 'Direction', 'Entry', 'Exit', 'Lots', 'P&L']

            st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)

            # Actions
            col_action1, col_action2 = st.columns(2)

            with col_action1:
                if st.button("🗑️ Clear All Trades", use_container_width=True):
                    if delete_user_trades(st.session_state.user_email):
                        st.success("✅ Tous les trades supprimés")
                        st.rerun()

            with col_action2:
                csv = display_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Export CSV",
                    data=csv,
                    file_name=f"trades_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("📭 Aucun trade enregistré. Ajoutez votre premier trade ci-dessous!")

        st.markdown("<br>", unsafe_allow_html=True)

        # ============================================
        # FORMULAIRE D'AJOUT DE TRADE (SOLUTION ROBUSTE)
        # ============================================
        st.markdown("#### ➕ Ajouter un Trade")

        with st.form("new_trade_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                trade_date = st.date_input("Date", datetime.now())
                trade_pair = st.selectbox("Asset", list(ASSET_CONFIG.keys()))
                trade_direction = st.radio("Direction", ["Long", "Short"], horizontal=True)
                trade_entry = st.number_input("Entry Price", min_value=0.0, value=0.0, step=0.01, format="%.4f")

            with col2:
                trade_exit = st.number_input("Exit Price", min_value=0.0, value=0.0, step=0.01, format="%.4f")
                trade_lots = st.number_input("Lots", min_value=0.0001, value=0.01, step=0.01, format="%.4f")
                trade_result = st.number_input("P&L (€)", value=0.0, step=10.0, help="Résultat net du trade")

            submitted = st.form_submit_button("✅ Valider et Ajouter", use_container_width=True)

            if submitted:
                # Validation
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
                        st.success("✅ Trade ajouté avec succès!")
                        time.sleep(0.5)  # Petit délai pour voir le message
                        st.rerun()
                else:
                    st.error("❌ Veuillez remplir Entry Price et Exit Price")

    # ============================================
    # TAB 4: ANALYTICS
    # ============================================
    with tab4:
        st.markdown("### 📊 Analytics & Performance")

        trades_df = get_user_trades(st.session_state.user_email)

        if not trades_df.empty:
            kpis = calculate_kpis(trades_df)

            # KPIs
            st.markdown("#### 📈 Statistiques Clés")

            kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

            with kpi_col1:
                st.metric("🎯 Winrate", f"{kpis['winrate']:.1f}%", f"{kpis['total_trades']} trades")

            with kpi_col2:
                st.metric("💰 Profit Factor", f"{kpis['profit_factor']:.2f}")

            with kpi_col3:
                st.metric("🟢 Biggest Win", f"+{kpis['biggest_win']:.2f} €")

            with kpi_col4:
                st.metric("🔴 Biggest Loss", f"{kpis['biggest_loss']:.2f} €")

            st.markdown("<br>", unsafe_allow_html=True)

            # Graphiques
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.markdown("#### 📈 Equity Curve")

                trades_df_sorted = trades_df.sort_values('date')
                trades_df_sorted['cumulative'] = trades_df_sorted['result'].cumsum() + st.session_state.capital_reel

                fig_equity = go.Figure()
                fig_equity.add_trace(go.Scatter(
                    x=trades_df_sorted['date'],
                    y=trades_df_sorted['cumulative'],
                    mode='lines+markers',
                    name='Equity',
                    line=dict(color='#00c9ff', width=3),
                    marker=dict(size=8, color='#00c9ff'),
                    fill='tozeroy',
                    fillcolor='rgba(0, 201, 255, 0.1)'
                ))

                fig_equity.add_hline(
                    y=st.session_state.capital_reel,
                    line_dash="dash",
                    line_color="white",
                    opacity=0.5
                )

                fig_equity.update_layout(
                    template="plotly_dark",
                    plot_bgcolor='#0e1117',
                    paper_bgcolor='#0e1117',
                    height=400,
                    xaxis_title="Date",
                    yaxis_title="Capital (€)",
                    hovermode='x unified'
                )

                st.plotly_chart(fig_equity, use_container_width=True)

            with chart_col2:
                st.markdown("#### 📊 Win/Loss Distribution")

                winning_count = len(trades_df[trades_df['result'] > 0])
                losing_count = len(trades_df[trades_df['result'] < 0])

                fig_pie = go.Figure(data=[go.Pie(
                    labels=['Wins', 'Losses'],
                    values=[winning_count, losing_count],
                    marker=dict(colors=['#00c9ff', '#ff4444']),
                    hole=0.5,
                    textinfo='label+percent',
                    textfont=dict(size=14, color='white')
                )])

                fig_pie.update_layout(
                    template="plotly_dark",
                    plot_bgcolor='#0e1117',
                    paper_bgcolor='#0e1117',
                    height=400
                )

                st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Stats détaillées
            st.markdown("#### 💵 Statistiques P&L")

            stats_col1, stats_col2, stats_col3 = st.columns(3)

            with stats_col1:
                total_pnl = trades_df['result'].sum()
                st.metric("Total P&L", f"{total_pnl:+.2f} €")

            with stats_col2:
                st.metric("Average Win", f"+{kpis['avg_win']:.2f} €")

            with stats_col3:
                st.metric("Average Loss", f"{kpis['avg_loss']:.2f} €")

        else:
            st.info("📭 Aucune donnée disponible. Ajoutez des trades dans le Journal!")

# ============================================
# ROUTING
# ============================================
if not st.session_state.authenticated:
    show_login_page()
else:
    show_main_app()
