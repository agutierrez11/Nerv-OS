import sys
from pathlib import Path

# --- CONFIGURACION DE RUTAS ---
ROOT_DIR = Path(__file__).parent.absolute()
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st
import csv
import os
import json
from dotenv import load_dotenv

# --- CONFIGURACION DE RUTAS NERV 2.0 ---
ROOT_DIR = Path(__file__).parent.absolute()
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# --- CONFIGURACION NERV 2.0 ---
from ui.styles import apply_styles
from ui.individual import render_individual_tab
from ui.batch import render_batch_tab
from ui.lab import render_lab_tab
from core.logger import logger

# Cargar entorno opcionalmente
if os.path.exists(".env"):
    load_dotenv()

# Configuración de página
st.set_page_config(
    page_title="NERV OS Intelligence",
    page_icon="🧠",
    layout="wide",
)

# Aplicar estilos CSS personalizados (FORCE LIGHT MODE)
st.markdown("""
<style>
    .main { background-color: #f8fafc !important; }
    .stApp { background-color: #f8fafc !important; color: #1e293b !important; }
    h1 { color: #1e3a8a !important; }
    h2, h3, .stSubheader { color: #1e3a8a !important; border-bottom: 2px solid #e2e8f0 !important; }
    label, [data-testid="stWidgetLabel"] p { color: #000000 !important; font-weight: 800 !important; }
    .stTextInput input, .stTextArea textarea { background-color: #ffffff !important; color: #000000 !important; border: 2px solid #94a3b8 !important; }
    .stButton > button { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%) !important; color: #ffffff !important; font-weight: 800 !important; }
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { visibility: hidden; display: none; }
</style>
""", unsafe_allow_html=True)

# Titulo y Header
st.title("🧠 NERV OS Intelligence")
st.caption("Forensic GTM Engine · v2.0 Production-Ready")
st.divider()

# Rutas base
BASE_DIR = Path(__file__).parent
COMPANIES_CSV = BASE_DIR / "companies.csv"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
USER_REGISTRY_FILE = BASE_DIR / "user_registry.json"

# Carga de datos
companies_data = []
if COMPANIES_CSV.exists():
    with open(COMPANIES_CSV, encoding="utf-8") as f:
        companies_data = list(csv.DictReader(f))
else:
    logger.error("No se encontro companies.csv")
    st.error("Archivo companies.csv no encontrado.")

# Funciones auxiliares de Registro Comercial
def load_users():
    if USER_REGISTRY_FILE.exists():
        try:
            with open(USER_REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando user_registry.json: {e}")
    return [{"name": "Antonio", "email": "", "role": "Sales Manager", "industry": "Fintech / Pagos"}]

def save_user(name, email, role, industry):
    users = load_users()
    if not any(u["email"].lower() == email.lower() for u in users):
        users.append({"name": name, "email": email, "role": role, "industry": industry})
        try:
            with open(USER_REGISTRY_FILE, "w", encoding="utf-8") as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando user_registry.json: {e}")

# --- PUERTA DE ACCESO ADMINISTRATIVO / ESPECIAL (BLOQUEO) ---
st.sidebar.title("🔒 Control de Acceso")
admin_password = os.getenv("NERV_PASSWORD", "nerv2026")
toku_password = os.getenv("TOKU_MODE_KEY", "toku2026")
entered_password = st.sidebar.text_input("Contraseña de Acceso", type="password", help="Ingresa la contraseña para desbloquear los módulos avanzados o especiales.")

is_admin = (entered_password == admin_password)
is_toku = (entered_password == toku_password)

# --- SECCION USUARIO COMERCIAL ---
st.sidebar.divider()
st.sidebar.title("👤 Identificación Comercial")

ROLES_COMERCIALES = [
    "-- Selecciona tu rol --",
    "BDR",
    "SDR",
    "Account Executive (AE)",
    "Inside Sales",
    "BDR Manager",
    "SDR Manager",
    "Sales Manager",
    "Key Account Manager (KAM)",
    "Head of Sales / VP Sales",
    "Revenue Operations (RevOps)",
    "Sales Engineer / Pre-Sales",
    "Customer Success Manager",
    "Channel / Partnerships",
    "Founder / CEO",
    "Otro",
]

INDUSTRIAS = [
    "-- Selecciona tu vertical --",
    "Fintech / Pagos",
    "SaaS / Software",
    "E-commerce / Retail",
    "Banca / Seguros",
    "Logística / Supply Chain",
    "Healthcare / Salud",
    "Real Estate / PropTech",
    "Educación / EdTech",
    "Manufactura / Industrial",
    "Energía / CleanTech",
    "Consultoría / Servicios Prof.",
    "Gobierno / Sector Público",
    "Otra",
]

user_active = None

if is_admin or is_toku:
    if is_admin:
        # Admin autologin — sin selector, sin contaminar DPO
        user_active = {
            "name": "Admin",
            "email": "admin@nerv.internal",
            "role": "Admin",
            "industry": "Test",
            "is_admin": True,   # ← flag para excluir del dataset DPO
            "is_toku": True,
            "vendedor_name": "Toku",
            "vendedor_url": "https://toku.com"
        }
        st.session_state.user_active = user_active
        st.sidebar.caption("🔐 Sesión Admin activa — los registros se marcarán como **test** y quedan excluidos del DPO.")
        st.sidebar.success("🔓 Acceso Administrador Autorizado")
    else:
        # Toku mode login
        user_active = {
            "name": "Toku Agent",
            "email": "agent@toku.com",
            "role": "Toku Hunter",
            "industry": "Fintech / Pagos",
            "is_admin": False,
            "is_toku": True,
            "vendedor_name": "Toku",
            "vendedor_url": "https://toku.com"
        }
        st.session_state.user_active = user_active
        st.sidebar.caption("🔐 Sesión Especial Toku activa.")
        st.sidebar.success("🔓 Acceso Toku Autorizado")
        
    # Mostrar todas las pestañas para el administrador y modo Toku
    tab_ind, tab_batch, tab_lab = st.tabs(["🎯 Analisis Individual", "📦 Procesamiento Batch", "🧪 NERV Lab"])
    
    with tab_ind:
        render_individual_tab(companies_data, OUTPUT_DIR, user_active=user_active)
        
    with tab_batch:
        render_batch_tab(companies_data, OUTPUT_DIR, user_active=user_active)
        
    with tab_lab:
        render_lab_tab(companies_data=companies_data, user_active=user_active, toku_mode=True)

else:
    # --- GATE DE IDENTIFICACION EN PANTALLA PRINCIPAL ---
    if "user_active" not in st.session_state:
        st.session_state.user_active = None
        
    if st.session_state.user_active is None:
        st.markdown("""
            <div style='background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); padding: 20px; border-radius: 10px; margin-bottom: 25px;'>
                <h2 style='color: white; margin: 0;'>👋 Bienvenido a NERV Intelligence</h2>
                <p style='color: #d1d5db; margin: 5px 0 0 0;'>
                    Por favor, identifícate para iniciar la demostración.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.info("Tus datos nos ayudan a personalizar la simulación de ventas.")
        col1, col2 = st.columns(2)
        with col1:
            rol_sel = st.selectbox("¿Cuál es tu rol?", options=ROLES_COMERCIALES, key="main_rol")
        with col2:
            ind_sel = st.selectbox("¿En qué vertical operas?", options=INDUSTRIAS, key="main_ind")
            
        if st.button("Ingresar al Laboratorio 🧬", type="primary"):
            if rol_sel != "-- Selecciona tu rol --":
                st.session_state.user_active = {
                    "name": rol_sel,
                    "email": "",
                    "role": rol_sel,
                    "industry": ind_sel if ind_sel != "-- Selecciona tu vertical --" else "General",
                    "is_admin": False,
                    "is_toku": False,
                }
                st.rerun()
            else:
                st.error("⚠️ Debes seleccionar un rol para continuar.")
    else:
        # Ya está identificado
        user_active = st.session_state.user_active
        
        # Botón de cambio de rol visible en la pantalla principal (header secundario)
        colA, colB = st.columns([0.7, 0.3])
        with colA:
            st.info(f"✅ Operando como **{user_active['role']}** en la vertical **{user_active['industry']}**")
        with colB:
            if st.button("🔄 Cambiar Rol / Vertical", use_container_width=True):
                st.session_state.user_active = None
                st.rerun()
            
        # En modo agnóstico: sin lista de Toku, el usuario ingresa la URL manualmente
        render_lab_tab(companies_data=None, user_active=user_active, toku_mode=False)

# Footer con observabilidad
st.sidebar.title("🛠️ Observabilidad")
st.sidebar.info(f"Dossiers en local: {len(list(OUTPUT_DIR.glob('*.md')))}")
if st.sidebar.button("Limpiar Cache Local"):
    if os.path.exists("nerv_cache.db"):
        os.remove("nerv_cache.db")
        st.sidebar.success("Cache eliminado.")
